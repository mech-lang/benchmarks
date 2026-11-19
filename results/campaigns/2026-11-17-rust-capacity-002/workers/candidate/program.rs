//! Checked native program calls. Inputs, outputs, aliases and managed teardown are explicit.
use super::*;
use mech_core::{ValueDataDraft as Data,snapshot::{ValueDraft,SnapshotValidationContext}};

pub fn run(request:&Value,artifact:&mech_engine::ProgramArtifact,catalog:&mech_core::FunctionCatalog,compile_seconds:f64)->Result<Value,String> {
    use mech_gpu::native_artifact::{JitProgramArtifact,NativeCompileLimits,NativeExecutionLimits,NativeProgramExecutionLimits};
    let encoded=mech_engine::encode_program_artifact_bytecode_v1(artifact).map_err(|e|format!("encode: {e:?}"))?;
    let decoded=mech_engine::decode_program_artifact_bytecode_v1(&encoded).map_err(|e|format!("decode: {e:?}"))?;
    let artifact=if request["backend"]=="bytecode" {&decoded} else {artifact};
    let limits:NativeCompileLimits=serde_json::from_value(request["compile_limits"].clone()).map_err(|e|e.to_string())?;
    let (jit,jit_seconds)=timed(||JitProgramArtifact::compile_with_limits(artifact,catalog,limits));
    let jit=jit.map_err(|e|format!("program JIT: {e:?}"))?;
    let policy=&request["launch_policy"];
    let mut library=mech_core::TargetMemoryProfile::current_resident_cpu().map_err(|e|format!("profile: {e:?}"))?.limits;
    let number=|key:&str|policy["library"][key].as_u64().ok_or_else(||format!("missing finite library policy {key}"));
    library.max_output_elements=Some(number("output_elements")?);library.max_output_bytes=Some(number("output_bytes")?);
    library.max_temporary_bytes=Some(number("temporary_bytes")?);library.max_cloned_bytes=Some(number("cloned_bytes")?);
    library.max_retained_nodes=Some(number("retained_nodes")?);library.max_compute_work=Some(number("compute_work")?);
    library.max_comparison_work=Some(number("comparison_work")?);
    let limits=NativeProgramExecutionLimits {execution:NativeExecutionLimits {
        max_work:policy["work"].as_u64().ok_or("missing work limit")?,
        max_transport_bytes:policy["transport_bytes"].as_u64().ok_or("missing transport limit")?,
        max_native_stack_bytes:policy["native_stack_bytes"].as_u64().ok_or("missing stack limit")?,},library};
    let budget=ManagedMemoryBudget::new(policy["memory_bytes"].as_u64().ok_or("missing memory limit")?);
    let output=artifact.outputs().iter().position(|o|o.name==request["output"].as_str().unwrap_or("result")).ok_or("missing named program output")?;
    let cases=request["application_cases"].as_array().ok_or("missing application cases")?;
    let mut results=vec![];
    for case in cases {
        let inputs=artifact.inputs().iter().map(|input|->Result<mech_core::Value,String>{
            let name=mech_engine::decode_source_input_name(&input.name).ok_or("invalid input name")?;
            let raw=std::fs::read(case[&name].as_str().ok_or("missing input file")?).map_err(|e|e.to_string())?;
            let shape=mech_core::shape_for_resolved_extents(artifact.schemas().get(input.schema).ok_or("missing schema")?,&[1,raw.len() as u64]).map_err(|e|format!("input shape: {e:?}"))?;
            let value=ValueDraft {schema:input.schema,shape_values:shape.parameter_values().into(),data:Data::Matrix(raw.into_iter().map(Data::U8).collect())}
                .finalize(&SnapshotValidationContext::new(artifact.schemas())).map_err(|e|format!("input draft: {e:?}"))?;
            let mut reservation=budget.reserve_capacity(value.memory_budget_admission_bytes(&budget).map_err(|e|format!("admission: {e:?}"))?).map_err(|e|format!("reservation: {e:?}"))?;
            value.into_memory_budget(&mut reservation).map_err(|e|format!("input budget: {e:?}"))
        }).collect::<Result<Vec<_>,_>>()?;
        let aliases:Vec<Box<[u8]>>=inputs.iter().map(|v|v.canonical_snapshot_bytes(artifact.schemas()).map_err(|e|format!("alias snapshot: {e:?}"))).collect::<Result<_,_>>()?;
        let mut outputs=vec![None;artifact.outputs().len()];
        for _ in 0..request["warmup"].as_u64().unwrap_or(0) {
            jit.evaluate_into(&inputs,&mut outputs,limits,&budget).map_err(|e|format!("warmup {}: {e:?}",case["name"]))?;
            outputs.fill(None);
        }
        let before=budget.used_bytes();let allocations=ALLOCS.load(Ordering::Relaxed);let bytes=BYTES.load(Ordering::Relaxed);
        let (report,seconds)=timed(||jit.evaluate_into(&inputs,&mut outputs,limits,&budget));
        let allocated=ALLOCS.load(Ordering::Relaxed)-allocations;let allocated_bytes=BYTES.load(Ordering::Relaxed)-bytes;
        let report=report.map_err(|e|format!("program call {}: {e:?}",case["name"]))?;
        let held=budget.used_bytes();
        for (input,alias) in inputs.iter().zip(&aliases) {
            if input.canonical_snapshot_bytes(artifact.schemas()).map_err(|e|format!("alias snapshot: {e:?}"))?!=*alias {return Err("held input or prefix alias changed".into());}
        }
        let value=outputs[output].as_ref().ok_or("native program did not publish named result")?;
        let ValueData::Matrix(matrix)=value.data() else {return Err("expected byte matrix result".into());};
        let SequenceView::U8(raw)=matrix.elements() else {return Err("expected u8 matrix result".into());};
        let hex:String=raw.iter().map(|b|format!("{b:02x}")).collect();
        drop(outputs);
        if budget.used_bytes()!=before {return Err("output cleanup did not restore retained input budget".into());}
        drop(inputs);drop(aliases);
        if budget.used_bytes()!=0 {return Err("managed application memory remains charged".into());}
        results.push(json!({"name":case["name"],"raw_hex":hex,"aliases_preserved":true,"metrics":{
            "native_program_call_seconds":seconds,"execution_allocations":allocated,"execution_allocated_bytes":allocated_bytes,
            "managed_inputs_bytes":before,"managed_published_bytes":held,"managed_after_drop_bytes":budget.used_bytes(),
            "execution_work":report.work,"comparison_work":report.comparison_work,"native_visits":report.visits,"transport_bytes":report.transport_bytes}}));
    }
    Ok(json!({"protocol":1,"outcome":"ok","application_results":results,"metrics":{"source_to_artifact_seconds":compile_seconds,"jit_compile_seconds":jit_seconds,"artifact_bytes":encoded.len()},"output_name":request["output"]}))
}
