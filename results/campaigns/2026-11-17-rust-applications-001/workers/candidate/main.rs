//! Versioned, single-request worker. The supervisor owns independent oracles.
use mech_core::snapshot::SequenceView;
use mech_core::{ManagedMemoryBudget, ReactiveInstanceId, ResidentValueRef, SchemaBody, ValueData};
use mech_engine::resident::{
    ActivationFacts, CapturedSignalInput, ResidentActivationOptions, activate_with_options,
};
use mech_runtime::RuntimeBuilder;
use serde_json::{Value, json};
use std::alloc::{GlobalAlloc, Layout, System};
use std::hint::black_box;
use std::io::{self, Read};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;

#[cfg(feature="native")]
mod program;

struct CountingAllocator;
static ALLOCS: AtomicU64 = AtomicU64::new(0);
static BYTES: AtomicU64 = AtomicU64::new(0);
unsafe impl GlobalAlloc for CountingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        ALLOCS.fetch_add(1, Ordering::Relaxed);
        BYTES.fetch_add(layout.size() as u64, Ordering::Relaxed);
        unsafe { System.alloc(layout) }
    }
    unsafe fn dealloc(&self, pointer: *mut u8, layout: Layout) {
        unsafe { System.dealloc(pointer, layout) }
    }
    unsafe fn realloc(&self, pointer: *mut u8, layout: Layout, size: usize) -> *mut u8 {
        ALLOCS.fetch_add(1, Ordering::Relaxed);
        BYTES.fetch_add(size as u64, Ordering::Relaxed);
        unsafe { System.realloc(pointer, layout, size) }
    }
}
#[global_allocator]
static ALLOCATOR: CountingAllocator = CountingAllocator;

fn elapsed(start: Instant) -> f64 {
    start.elapsed().as_secs_f64()
}
fn timed<T>(work: impl FnOnce() -> T) -> (T, f64) {
    let started = Instant::now();
    let output = work();
    (output, elapsed(started))
}
fn data_json(data: &ValueData) -> Result<Value, String> {
    Ok(match data {
        ValueData::F64(n) => json!(n.to_f64()),
        ValueData::F32(n) => json!(n.to_f32()),
        ValueData::U8(n) => json!(n), ValueData::U16(n) => json!(n),
        ValueData::U32(n) => json!(n), ValueData::U64(n) => json!(n),
        ValueData::I8(n) => json!(n), ValueData::I16(n) => json!(n),
        ValueData::I32(n) => json!(n), ValueData::I64(n) => json!(n),
        ValueData::Bool(n) => json!(n), ValueData::String(n) => json!(n),
        ValueData::Index(n) => json!(n), ValueData::Atom => Value::Null,
        ValueData::Option(n) => match n { Some(n) => data_json(n)?, None => Value::Null },
        ValueData::Tuple(fields) => Value::Array(fields.iter().map(data_json).collect::<Result<_,_>>()?),
        ValueData::Record(record) => Value::Array(record.fields().iter().map(data_json).collect::<Result<_,_>>()?),
        other => return Err(format!("unsupported nested observation: {other:?}")),
    })
}
fn sequence_json(sequence: SequenceView<'_>) -> Result<Vec<Value>, String> {
    sequence.to_values().iter().map(data_json).collect()
}
fn observation(value: mech_core::Value) -> Result<Value, String> {
    Ok(match value.data() {
        ValueData::Matrix(matrix) => {
            let schemas = value.schemas().ok_or("matrix schemas missing")?;
            let SchemaBody::Matrix { dimensions, .. } = schemas.entry(value.schema()).ok_or("matrix schema missing")?.schema().body() else {
                return Err("invalid matrix schema".into());
            };
            let shape: Vec<u64> = dimensions.iter().map(|dimension| value.shape().resolve_dimension(dimension).unwrap()).collect();
            json!({"kind":"matrix","shape":shape,"values":sequence_json(matrix.elements())?})
        }
        ValueData::Table(table) => {
            let schemas = value.schemas().ok_or("table schemas missing")?;
            let SchemaBody::Table { columns, .. } = schemas.entry(value.schema()).ok_or("table schema missing")?.schema().body() else {
                return Err("invalid table schema".into());
            };
            let values: Vec<Vec<Value>> = (0..table.len()).map(|i| sequence_json(table.column(i).unwrap())).collect::<Result<_,_>>()?;
            let rows: Vec<Vec<Value>> = (0..values.first().map_or(0,Vec::len)).map(|row| values.iter().map(|column| column[row].clone()).collect()).collect();
            json!({"kind":"table","columns":columns.iter().map(|c| c.name.as_str()).collect::<Vec<_>>(),"rows":rows})
        }
        ValueData::Set(set) => {
            let mut elements: Vec<Value> = set.elements().iter().map(|v| data_json(v.data())).collect::<Result<_,_>>()?;
            elements.sort_by(|a,b| match (a.as_f64(),b.as_f64()) { (Some(a),Some(b)) => a.total_cmp(&b), _ => a.to_string().cmp(&b.to_string()) });
            json!({"kind":"set","values":elements})
        }
        data => json!({"kind":"scalar","value":data_json(data)?}),
    })
}
fn published(instance: &mech_engine::resident::ReactiveInstance, output: usize, request: &Value) -> Result<Value, String> {
    if request["observe_state"] == true {
        use mech_engine::resident::ResidentValueBorrow;
        let mut state=vec![0.0f64;12];
        for slot in instance.plan.slots.iter().filter(|s| s.role==mech_engine::SlotRole::State) {
            let ResidentValueBorrow::F64 {values,..}=instance.state_borrow(slot.artifact_id).ok_or("state missing")? else {return Err("expected f64 state".into());};
            match values.len() {3=>state[..3].copy_from_slice(values),9=>state[3..].copy_from_slice(values),_=>return Err("unexpected EKF state".into())}
        }
        return Ok(json!({"kind":"matrix","shape":[1,12],"values":state}));
    }
    if instance.output_borrow(output).is_none() { return Ok(json!({"kind":"unpublished"})); }
    observation(instance.copied_output(output).map_err(|e| format!("output: {e:?}"))?)
}
enum Frame { F64(Vec<f64>), String(Vec<String>) }
impl Frame {
    fn parse(frame: &Value, kind: &str) -> Result<Self,String> {
        let values=frame.as_array().ok_or("frame must be an array")?;
        match kind {
            "string" => Ok(Self::String(values.iter().map(|v| v.as_str().map(str::to_owned).ok_or("input must be string".into())).collect::<Result<_,String>>()?)),
            "f64" => Ok(Self::F64(values.iter().map(|v| v.as_f64().ok_or("input must be f64".into())).collect::<Result<_,String>>()?)),
            _ => Err("unsupported input kind".into()),
        }
    }
    fn borrow(&self) -> ResidentValueRef<'_> {
        match self { Self::F64(v)=>ResidentValueRef::F64(v), Self::String(v)=>ResidentValueRef::String(v) }
    }
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let result = std::panic::catch_unwind(|| {
        let request: Value = serde_json::from_str(&input).map_err(|e| e.to_string())?;
        run(&request)
    });
    let response = match result {
        Ok(Ok(value)) => value,
        Ok(Err(error)) => json!({"protocol":1,"outcome":"error","error":error}),
        Err(_) => json!({"protocol":1,"outcome":"crash","error":"worker panicked; see stderr"}),
    };
    println!("{}", response);
}

fn run(request: &Value) -> Result<Value, String> {
    if request["protocol"] != 1 {
        return Err("unsupported protocol".into());
    }
    let source = request["source"].as_str().ok_or("missing source")?;
    let schedule = request["schedule"].as_array().ok_or("missing schedule")?;
    let frames: Vec<Frame> = schedule.iter().map(|f| Frame::parse(f,request["input_kind"].as_str().unwrap_or("f64"))).collect::<Result<_,_>>()?;
    if frames.is_empty() {
        return Err("empty schedule".into());
    }
    let frozen = request["compiler_profile"] == "frozen-ekf-v1";
    let catalog = if frozen {mech_engine::__resident::frozen_ekf_compiler_catalog().map_err(|e| format!("EKF catalog: {e:?}"))?} else {mech_stdlib::source_catalog()};
    let (artifact, compile_seconds) = if frozen {
        let (product, seconds)=timed(|| mech_engine::__resident::compile_frozen_ekf_source(source, &mut mech_engine::__resident::FrozenEkfCompilationServices::default()));
        (product.map_err(|e| format!("frozen EKF compile: {e:?}"))?.source_artifact, seconds)
    } else {
        let mut compiler=RuntimeBuilder::new().function_catalog(catalog.clone()).build_compiler().map_err(|e| format!("compiler: {e:?}"))?;
        let (product,seconds)=timed(|| compiler.compile_source(source));
        (product.map_err(|e| format!("compile: {e:?}"))?.artifact().clone(),seconds)
    };
    let artifact=&artifact;
    if request["action"] == "application_jit" {
        #[cfg(feature="native")]
        return program::run(request,artifact,&catalog,compile_seconds);
        #[cfg(not(feature="native"))]
        return Err("native program backend was not built".into());
    }
    if request["action"] == "native_generate" {
        #[cfg(feature = "native")]
        {
            let workspace =
                std::path::Path::new(request["workspace"].as_str().ok_or("missing workspace")?);
            let destination = std::path::Path::new(
                request["native_directory"]
                    .as_str()
                    .ok_or("missing native directory")?,
            );
            let started = Instant::now();
            let generated = if request["native_kind"]=="program" {
                let encoded=mech_engine::encode_program_artifact_bytecode_v1(artifact).map_err(|e|format!("encode: {e:?}"))?;
                let decoded=mech_engine::decode_program_artifact_bytecode_v1(&encoded).map_err(|e|format!("decode: {e:?}"))?;
                let artifact=if request["backend"]=="bytecode" {&decoded} else {artifact};
                let limits:mech_gpu::native_artifact::NativeCompileLimits=if request["compile_limits"].is_object() {serde_json::from_value(request["compile_limits"].clone()).map_err(|e|e.to_string())?} else {Default::default()};
                let generated=mech_gpu::native_artifact::generate_linked_program_application_with_limits(workspace,destination,"mech-bench-native",artifact,&catalog,source.as_bytes(),limits).map_err(|e| format!("native program generation: {e:?}"))?;
                let cases=write_application_cases(request,artifact,generated.root())?;
                return Ok(json!({"protocol":1,"outcome":"ok","source_to_artifact_seconds":compile_seconds,"native_generation_seconds":elapsed(started),"metadata":generated.metadata(),"root":generated.root(),"manifest":generated.manifest_path(),"output_names":artifact.outputs().iter().map(|o|o.name.as_str()).collect::<Vec<_>>(),"application_cases":cases}));
            } else {
                mech_gpu::native_artifact::generate_linked_application(workspace,destination,"mech-bench-native",artifact,&catalog,source.as_bytes()).map_err(|e| format!("native scalar generation: {e:?}"))?
            };
            return Ok(
                json!({"protocol":1,"outcome":"ok","source_to_artifact_seconds":compile_seconds,
                "native_generation_seconds":elapsed(started),"metadata":generated.metadata(),
                "root":generated.root(),"manifest":generated.manifest_path(),
                "output_names":artifact.outputs().iter().map(|o| o.name.as_str()).collect::<Vec<_>>()}),
            );
        }
        #[cfg(not(feature = "native"))]
        return Err("native generator not included; build worker with --native".into());
    }
    let output_name = request["output"].as_str().ok_or("missing named output")?;
    let output = artifact
        .outputs()
        .iter()
        .position(|output| output.name == output_name)
        .ok_or_else(|| format!("missing output {output_name}"))?;
    let (bytes, encode_seconds) =
        timed(|| mech_engine::encode_program_artifact_bytecode_v1(artifact));
    let bytes = bytes.map_err(|e| format!("encode: {e:?}"))?;
    let (decoded, decode_seconds) =
        timed(|| mech_engine::decode_program_artifact_bytecode_v1(&bytes));
    let decoded = decoded.map_err(|e| format!("decode: {e:?}"))?;
    let artifact = if request["backend"] == "bytecode" {
        &decoded
    } else {
        artifact
    };
    if request["backend"] == "jit" {
        #[cfg(feature="native")]
        return run_jit(request,artifact,&catalog,&frames,output,compile_seconds,bytes.len(),encode_seconds,decode_seconds);
        #[cfg(not(feature="native"))]
        return Err("JIT not included; build with --native".into());
    }
    let budget = ManagedMemoryBudget::new(1 << 34);
    let activate_instance = || {
        activate_with_options(
            ReactiveInstanceId::new(0xbec, 0),
            artifact,
            &catalog,
            &ActivationFacts::default(),
            ResidentActivationOptions {
                memory_budget: Some(budget.clone()),
                ..ResidentActivationOptions::default()
            },
        )
        .map_err(|e| format!("activate: {e:?}"))
    };
    let verify = request["action"] == "verify";
    let mut initial_turn_seconds = 0.0;
    if !verify {
        let mut warm = activate_instance()?;
        for index in 0..request["warmup"].as_u64().unwrap_or(0) as usize {
            let inputs = warm.plan.inputs.first().map(|input| CapturedSignalInput {
                slot: input.slot,
                value: frames[index % frames.len()].borrow(),
            });
            if index == 0 {
                let (result, duration) = timed(|| warm.turn(inputs.as_slice()));
                result.map_err(|e| format!("initial turn: {e:?}"))?;
                initial_turn_seconds = duration;
            } else {
                warm.turn(inputs.as_slice())
                    .map_err(|e| format!("warmup: {e:?}"))?;
            }
        }
        drop(warm);
    }
    let (instance, activation_seconds) = timed(activate_instance);
    let mut instance = instance?;
    let activation_bytes = budget.used_bytes();
    if instance.plan.inputs.len() > 1 {
        return Err("adapter admits one typed scalar/vector input".into());
    }
    let slot = instance.plan.inputs.first().map(|input| input.slot);
    let iterations = request["iterations"].as_u64().ok_or("missing iterations")? as usize;
    let mut outputs = Vec::new();
    let mut before_execution = Vec::new();
    let mut touched = 0u64;
    let mut changed = 0u64;
    let mut dirty = 0u64;
    let mut rejected = 0u64;
    let mut suspensions = 0u64;
    if iterations == 0 || iterations > 10_000_000 {
        return Err("invalid iteration count".into());
    }
    let retain = request["retain_snapshots"] == true;
    let mut owned_snapshots = Vec::with_capacity(if retain { iterations } else { 0 });
    let allocations_before = ALLOCS.load(Ordering::Relaxed);
    let bytes_before = BYTES.load(Ordering::Relaxed);
    let (execution_result, execution_seconds) = timed(|| -> Result<(), String> {
        for index in 0..iterations {
            let frame = &frames[index % frames.len()];
            let inputs = slot.map(|slot| CapturedSignalInput {
                slot,
                value: frame.borrow(),
            });
            if verify && index > 0 {
                before_execution.push(published(&instance, output, request)?);
            }
            if request["abort_before_accept"] == true {
                let previous = if verify {
                    Some(instance.published_state_hash())
                } else {
                    None
                };
                drop(
                    instance
                        .prepare_turn(inputs.as_slice())
                        .map_err(|e| format!("prepare abort: {e:?}"))?,
                );
                if previous.is_some_and(|hash| instance.published_state_hash() != hash) {
                    return Err("aborted candidate changed published state".into());
                }
            }
            if request["reject_before_accept"] == true {
                let previous=instance.published_state_hash();
                // A wrong-sized capture must fail admission before publication.
                let invalid=[0.0f64; 2];
                let bad=slot.map(|slot| CapturedSignalInput {slot,value:ResidentValueRef::F64(&invalid)});
                if instance.prepare_turn(bad.as_slice()).is_ok() {return Err("invalid shape was accepted".into());}
                if instance.published_state_hash()!=previous {return Err("rejected candidate changed published state".into());}
                rejected+=1;
            }
            let summary = instance
                .turn(inputs.as_slice())
                .map_err(|e| format!("turn: {e:?}"))?;
            black_box(summary.state_hash);
            if instance.has_ready_continuation() {suspensions+=1;}
            touched += summary.touched_slots as u64;
            changed += summary.changed_slots as u64;
            dirty += summary.dirty_nodes as u64;
            // Retention is a separate declared boundary, never silently part of a borrowed-output turn.
            if retain {
                owned_snapshots.push(
                    instance
                        .copied_output(output)
                        .map_err(|e| format!("retain: {e:?}"))?,
                );
            }
            if verify {
                outputs.push(published(&instance, output, request)?);
            }
        }
        Ok(())
    });
    execution_result?;
    let execution_allocations = ALLOCS.load(Ordering::Relaxed) - allocations_before;
    let execution_allocated_bytes = BYTES.load(Ordering::Relaxed) - bytes_before;
    let retained_bytes = budget.used_bytes();
    let (_, borrow_seconds) = timed(|| black_box(instance.output_borrow(output)));
    let (value, snapshot_seconds) = timed(|| instance.copied_output(output));
    let final_output = if request["observe_state"]==true {drop(value);published(&instance,output,request)?} else if instance.output_borrow(output).is_none() {json!({"kind":"unpublished"})} else {observation(value.map_err(|e| format!("final output: {e:?}"))?)?};
    let snapshot_outputs: Vec<Value> = if verify {
        owned_snapshots
            .iter()
            .cloned()
            .map(observation)
            .collect::<Result<_, _>>()?
    } else {
        vec![]
    };
    let planned_arena_bytes: u64 = instance
        .plan
        .memory_plan
        .arenas
        .iter()
        .map(|arena| arena.capacity_bytes)
        .sum();
    let node_count = instance.plan.execution_node_count();
    let started = Instant::now();
    drop(instance);
    let after_instance_drop_bytes = budget.used_bytes();
    drop(owned_snapshots);
    let teardown_seconds = elapsed(started);
    let after_drop_bytes = budget.used_bytes();
    let mut usage: libc::rusage = unsafe { std::mem::zeroed() };
    unsafe {
        libc::getrusage(libc::RUSAGE_SELF, &mut usage);
    }
    let rss_bytes = if cfg!(target_os = "macos") {
        usage.ru_maxrss as u64
    } else {
        usage.ru_maxrss as u64 * 1024
    };
    Ok(json!({"protocol":1,"outcome":"ok", "outputs": outputs,
        "before_execution":before_execution,"retained_outputs":snapshot_outputs,"final_output":final_output,
        "output_index":output,"input_count":usize::from(slot.is_some()),"iterations":iterations,
        "output_name":output_name,
        "metrics": {"source_to_artifact_seconds":compile_seconds,"artifact_encode_seconds":encode_seconds,
            "artifact_decode_seconds":decode_seconds,"activation_seconds":activation_seconds,
            "resident_turn_seconds":execution_seconds / iterations as f64,"initial_turn_seconds":initial_turn_seconds,
            "execution_block_seconds":execution_seconds,"borrow_output_seconds":borrow_seconds,
            "owned_snapshot_seconds":snapshot_seconds,"teardown_seconds":teardown_seconds,
            "artifact_bytes":bytes.len(),"execution_nodes":node_count,
            "managed_activation_bytes":activation_bytes,"managed_retained_bytes":retained_bytes,
            "managed_after_drop_bytes":after_drop_bytes,"planned_arena_bytes":planned_arena_bytes,
            "managed_after_instance_drop_bytes":after_instance_drop_bytes,
            "execution_allocations":execution_allocations,"execution_allocated_bytes":execution_allocated_bytes,
            "worker_process_peak_rss_bytes":rss_bytes,"touched_slots":touched,"changed_slots":changed,"dirty_nodes":dirty,"rejected_turns":rejected,"suspended_turns":suspensions}}))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::Cell;
    use std::rc::Rc;
    use std::time::Duration;

    #[test]
    fn setup_and_output_destruction_are_outside_the_measured_interval() {
        struct SlowDrop(Rc<Cell<bool>>);
        impl Drop for SlowDrop {
            fn drop(&mut self) {
                std::thread::sleep(Duration::from_millis(40));
                self.0.set(true);
            }
        }
        let dropped = Rc::new(Cell::new(false));
        let lifecycle = Instant::now();
        std::thread::sleep(Duration::from_millis(40)); // preparation
        let (output, measured) = timed(|| {
            std::thread::sleep(Duration::from_millis(2)); // execution
            SlowDrop(dropped.clone())
        });
        assert!(
            !dropped.get(),
            "timing helper must retain its output past the stop time"
        );
        drop(output);
        assert!(dropped.get());
        assert!(
            lifecycle.elapsed().as_secs_f64() - measured >= 0.075,
            "preparation and output destruction must not enter the measured interval"
        );
    }
}

#[cfg(feature="native")]
fn run_jit(request: &Value, artifact: &mech_engine::ProgramArtifact, catalog: &mech_core::FunctionCatalog,
    frames: &[Frame], output: usize, compile_seconds:f64, artifact_bytes:usize, encode_seconds:f64, decode_seconds:f64) -> Result<Value,String> {
    use mech_engine::native_artifact::{NativeScalarValue,lower_pure_native_artifact};
    use mech_gpu::native_artifact::{JitArtifact,NativeExecutionLimits};
    let (plan,lower_seconds)=timed(|| lower_pure_native_artifact(artifact,catalog));
    let plan=plan.map_err(|e|format!("native lowering: {e:?}"))?;
    let (jit,jit_compile_seconds)=timed(||JitArtifact::compile(&plan));
    let jit=jit.map_err(|e|format!("JIT compile: {e:?}"))?;
    if plan.inputs().len()!=1 {return Err("JIT adapter expects one scalar input".into());}
    let args:Vec<Vec<NativeScalarValue>>=frames.iter().map(|f| match f {
        Frame::F64(v) if v.len()==1=>Ok(vec![NativeScalarValue::F64(mech_core::snapshot::F64Bits::from_f64(v[0]))]),
        _=>Err("JIT adapter expects scalar f64 frames".to_owned())
    }).collect::<Result<_,_>>()?;
    let observe=|v:&NativeScalarValue|->Result<Value,String>{match v {
        NativeScalarValue::F64(n)=>Ok(json!({"kind":"scalar","value":n.to_f64()})),
        _=>Err("JIT adapter expects f64 result".into()),
    }};
    let budget=ManagedMemoryBudget::new(1<<34);
    let mut values=vec![NativeScalarValue::F64(mech_core::snapshot::F64Bits::from_f64(0.0));plan.outputs().len()];
    let verify=request["action"]=="verify";
    if !verify {
        for i in 0..request["warmup"].as_u64().unwrap_or(0) as usize {
            jit.evaluate_into(&args[i%args.len()],&mut values,NativeExecutionLimits::default(),Some(&budget)).map_err(|e|format!("JIT warmup: {e:?}"))?;
        }
    }
    let iterations=request["iterations"].as_u64().ok_or("missing iteration count")? as usize;
    if iterations==0 || iterations>10_000_000 {return Err("invalid iteration count".into());}
    let mut outputs=Vec::new();let mut before=Vec::new();
    let allocations_before=ALLOCS.load(Ordering::Relaxed);let bytes_before=BYTES.load(Ordering::Relaxed);
    let started=Instant::now();
    for i in 0..iterations {
        if verify && i>0 {before.push(observe(&values[output])?);}
        let report=jit.evaluate_into(&args[i%args.len()],&mut values,NativeExecutionLimits::default(),Some(&budget)).map_err(|e|format!("JIT evaluate: {e:?}"))?;
        black_box(report);
        if verify {outputs.push(observe(&values[output])?);}
    }
    let execution_seconds=elapsed(started);
    let allocations=ALLOCS.load(Ordering::Relaxed)-allocations_before;
    let allocated_bytes=BYTES.load(Ordering::Relaxed)-bytes_before;
    let final_output=observe(&values[output])?;
    let started=Instant::now();drop(jit);drop(values);let teardown_seconds=elapsed(started);
    Ok(json!({"protocol":1,"outcome":"ok","outputs":outputs,"before_execution":before,"retained_outputs":[],
        "iterations":iterations,"output_name":request["output"],"final_output":final_output,
        "metrics":{"jit_invocation_seconds":execution_seconds/iterations as f64,"execution_block_seconds":execution_seconds,
            "source_to_artifact_seconds":compile_seconds,"native_lower_seconds":lower_seconds,"jit_compile_seconds":jit_compile_seconds,
            "artifact_encode_seconds":encode_seconds,"artifact_decode_seconds":decode_seconds,"artifact_bytes":artifact_bytes,
            "managed_after_drop_bytes":budget.used_bytes(),"teardown_seconds":teardown_seconds,
            "execution_allocations":allocations,"execution_allocated_bytes":allocated_bytes}}))
}

#[cfg(feature="native")]
fn write_application_cases(request:&Value,artifact:&mech_engine::ProgramArtifact,root:&std::path::Path)->Result<Value,String> {
    use mech_core::{ValueDataDraft as Data,snapshot::ValueDraft};
    let Some(cases)=request["application_cases"].as_array() else {return Ok(json!([]));};
    let mut receipts=vec![];
    std::fs::create_dir(root.join("cases")).map_err(|e|e.to_string())?;
    for (ordinal,case) in cases.iter().enumerate() {
        let drafts=artifact.inputs().iter().map(|input| -> Result<ValueDraft,String> {
            let name=mech_engine::decode_source_input_name(&input.name).ok_or("input name missing")?;
            let values=case[&name].as_array().ok_or_else(||format!("missing input {name}"))?;
            let bytes=values.iter().map(|v|v.as_u64().filter(|n|*n<=255).map(|n|Data::U8(n as u8)).ok_or("expected u8".to_owned())).collect::<Result<Vec<_>,_>>()?;
            let shape=mech_core::shape_for_resolved_extents(artifact.schemas().get(input.schema).ok_or("schema missing")?,&[1,bytes.len() as u64]).map_err(|e|format!("shape: {e:?}"))?;
            Ok(ValueDraft {schema:input.schema,shape_values:shape.parameter_values().into(),data:Data::Matrix(bytes.into())})
        }).collect::<Result<Vec<_>,_>>()?;
        let relative=format!("cases/{ordinal}.json");
        std::fs::write(root.join(&relative),serde_json::to_vec(&drafts).map_err(|e|e.to_string())?).map_err(|e|e.to_string())?;
        receipts.push(json!({"name":case["name"],"input":relative}));
    }
    Ok(json!(receipts))
}
