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
fn observation(value: mech_core::Value) -> Result<Value, String> {
    let result = match value.data() {
        ValueData::F64(number) => json!({"kind":"scalar", "value":number.to_f64()}),
        ValueData::Matrix(matrix) => {
            let schemas = value.schemas().ok_or("matrix schemas missing")?;
            let SchemaBody::Matrix { dimensions, .. } = schemas
                .entry(value.schema())
                .ok_or("matrix schema missing")?
                .schema()
                .body()
            else {
                return Err("invalid matrix schema".into());
            };
            let shape: Vec<u64> = dimensions
                .iter()
                .map(|dimension| value.shape().resolve_dimension(dimension).unwrap())
                .collect();
            let elements: Vec<f64> = match matrix.elements() {
                SequenceView::F64(values) => values.iter().map(|n| n.to_f64()).collect(),
                _ => return Err("adapter expects f64 matrix output".into()),
            };
            json!({"kind":"matrix","shape":shape,"values":elements})
        }
        ValueData::Set(set) => {
            let mut elements = Vec::new();
            for value in set.elements() {
                let ValueData::F64(number) = value.data() else {
                    return Err("adapter expects f64 set output".into());
                };
                elements.push(number.to_f64());
            }
            elements.sort_by(f64::total_cmp);
            json!({"kind":"set","values":elements})
        }
        other => {
            return Err(format!(
                "adapter does not observe this output type: {other:?}"
            ));
        }
    };
    Ok(result)
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
    let frames: Vec<Vec<f64>> = schedule
        .iter()
        .map(|frame| {
            frame
                .as_array()
                .ok_or("frame must be an array")?
                .iter()
                .map(|n| n.as_f64().ok_or("input must be f64".to_string()))
                .collect()
        })
        .collect::<Result<_, _>>()?;
    if frames.is_empty() {
        return Err("empty schedule".into());
    }
    let catalog = mech_stdlib::source_catalog();
    let mut compiler = RuntimeBuilder::new()
        .function_catalog(catalog.clone())
        .build_compiler()
        .map_err(|e| format!("compiler: {e:?}"))?;
    let (product, compile_seconds) = timed(|| compiler.compile_source(source));
    let product = product.map_err(|e| format!("compile: {e:?}"))?;
    let artifact = product.artifact();
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
            let generated = mech_gpu::native_artifact::generate_linked_application(
                workspace,
                destination,
                "mech-bench-native",
                artifact,
                &catalog,
                source.as_bytes(),
            )
            .map_err(|error| format!("native generation: {error:?}"))?;
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
                value: ResidentValueRef::F64(&frames[index % frames.len()]),
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
        return Err("adapter admits one scalar/vector f64 input".into());
    }
    let slot = instance.plan.inputs.first().map(|input| input.slot);
    let iterations = request["iterations"].as_u64().ok_or("missing iterations")? as usize;
    let mut outputs = Vec::new();
    let mut before_execution = Vec::new();
    let mut touched = 0u64;
    let mut changed = 0u64;
    let mut dirty = 0u64;
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
                value: ResidentValueRef::F64(frame),
            });
            if verify && index > 0 {
                before_execution.push(observation(
                    instance
                        .copied_output(output)
                        .map_err(|e| format!("before output: {e:?}"))?,
                )?);
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
            let summary = instance
                .turn(inputs.as_slice())
                .map_err(|e| format!("turn: {e:?}"))?;
            black_box(summary.state_hash);
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
                outputs.push(observation(
                    instance
                        .copied_output(output)
                        .map_err(|e| format!("output: {e:?}"))?,
                )?);
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
    let value = value.map_err(|e| format!("final output: {e:?}"))?;
    let final_output = observation(value)?;
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
            "worker_process_peak_rss_bytes":rss_bytes,"touched_slots":touched,"changed_slots":changed,"dirty_nodes":dirty}}))
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
