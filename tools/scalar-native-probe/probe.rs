//! Primary scalar entry versus canonical managed transport: correctness, latency, allocations.
#![cfg(feature = "canonical-native-program")]
use mech_core::{
    ManagedMemoryBudget, Value, ValueDataDraft,
    snapshot::{SnapshotValidationContext, ValueDraft},
};
use mech_engine::{CanonicalSourceFrontend, ProgramArtifact, SourceDocumentOutputKind};
use mech_gpu::native_artifact::{
    JitProgramArtifact, NativeExecutionLimits, NativeProgramExecutionLimits,
};
use mech_syntax::document::{
    AstNode, DocumentId, DocumentSyntax, ParseConfig, Revision, TextSnapshot,
    parse_canonical_document,
};
fn artifacts(source: &str) -> ([ProgramArtifact; 2], usize) {
    artifacts_mode(source, false)
}
fn artifacts_mode(source: &str, interactive: bool) -> ([ProgramArtifact; 2], usize) {
    let parsed = parse_canonical_document(
        TextSnapshot::new(DocumentId(0x50524f47), Revision(1), source).unwrap(),
        ParseConfig::default(),
    );
    assert!(
        parsed.is_strictly_clean(),
        "{source}: {:?}",
        parsed.diagnostics
    );
    let syntax = DocumentSyntax::cast(parsed.syntax()).unwrap();
    let product = if interactive {
        CanonicalSourceFrontend
            .compile_interactive_document_with_catalog(&syntax, mech_stdlib::source_catalog())
    } else {
        CanonicalSourceFrontend
            .compile_document_with_catalog(&syntax, mech_stdlib::source_catalog())
    }
    .unwrap();
    let last = product
        .document_outputs()
        .iter()
        .rev()
        .find(|out| out.kind == SourceDocumentOutputKind::Program)
        .unwrap()
        .output as usize;
    let original = product.compile_artifact().unwrap();
    let decoded = mech_engine::decode_program_artifact_bytecode_v1(
        &mech_engine::encode_program_artifact_bytecode_v1(&original).unwrap(),
    )
    .unwrap();
    ([original, decoded], last)
}
fn limits() -> NativeProgramExecutionLimits {
    let mut library = mech_core::TargetMemoryProfile::current_resident_cpu()
        .unwrap()
        .limits;
    // Explicit finite qualification policy, NOT a default-budget/performance claim.
    library.max_compute_work = Some(134_217_728);
    library.max_comparison_work = Some(1_000_000);
    library.max_temporary_bytes = Some(128 * 1024 * 1024);
    NativeProgramExecutionLimits {
        execution: NativeExecutionLimits {
            max_work: 1_000_000_000,
            ..NativeExecutionLimits::default()
        },
        library,
    }
}
fn inputs(
    artifact: &ProgramArtifact,
    named: &[(&str, ValueDataDraft)],
    memory: &ManagedMemoryBudget,
) -> Vec<Value> {
    artifact
        .inputs()
        .iter()
        .map(|input| {
            let name = mech_engine::decode_source_input_name(&input.name).unwrap();
            let data = named
                .iter()
                .find(|(key, _)| *key == name)
                .unwrap_or_else(|| panic!("missing {name}"))
                .1
                .clone();
            let shape_values = match &data {
                ValueDataDraft::Matrix(values) => mech_core::shape_for_resolved_extents(
                    artifact.schemas().get(input.schema).unwrap(),
                    &[1, values.len() as u64],
                )
                .unwrap()
                .parameter_values()
                .to_vec()
                .into_boxed_slice(),
                _ => Box::new([]),
            };
            let value = ValueDraft {
                schema: input.schema,
                shape_values,
                data,
            }
            .finalize(&SnapshotValidationContext::new(artifact.schemas()))
            .unwrap();
            let mut reservation = memory
                .reserve_capacity(value.memory_budget_admission_bytes(memory).unwrap())
                .unwrap();
            value.into_memory_budget(&mut reservation).unwrap()
        })
        .collect()
}
struct CountingAllocator;
static PROBE_ALLOCS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
unsafe impl std::alloc::GlobalAlloc for CountingAllocator {
    unsafe fn alloc(&self, layout: std::alloc::Layout) -> *mut u8 {
        PROBE_ALLOCS.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        unsafe { std::alloc::System.alloc(layout) }
    }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: std::alloc::Layout) {
        unsafe { std::alloc::System.dealloc(ptr, layout) }
    }
    unsafe fn realloc(&self, ptr: *mut u8, layout: std::alloc::Layout, size: usize) -> *mut u8 {
        PROBE_ALLOCS.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        unsafe { std::alloc::System.realloc(ptr, layout, size) }
    }
}
#[global_allocator]
static PROBE_ALLOCATOR: CountingAllocator = CountingAllocator;

#[test]
#[ignore = "explicit serial native scalar latency and allocation measurement"]
fn scalar_entry_latency_and_allocations() {
    use mech_engine::native_artifact::{NativeScalarValue, lower_pure_native_artifact};
    use mech_gpu::native_artifact::JitArtifact;
    use std::sync::atomic::Ordering::Relaxed;
    for operations in [1, 32, 256] {
        let source = format!("x<u64>{}\n", " + 1u64".repeat(operations));
        let (variants, last) = artifacts(&source);
        for (variant, artifact) in variants.into_iter().enumerate() {
            let catalog = mech_stdlib::source_catalog();
            let plan = lower_pure_native_artifact(&artifact, &catalog).unwrap();
            let scalar = JitArtifact::compile(&plan).unwrap();
            let canonical = JitProgramArtifact::compile(&artifact, &catalog).unwrap();
            let memory = ManagedMemoryBudget::new(256 * 1024 * 1024);
            let args = inputs(&artifact, &[("x", ValueDataDraft::U64(7))], &memory);
            let scalar_args = [NativeScalarValue::U64(7)];
            let mut scalar_outputs = vec![NativeScalarValue::U64(0); artifact.outputs().len()];
            let mut outputs = vec![None; artifact.outputs().len()];
            let policy = limits();
            // Warm both paths without retaining output storage between invocations.
            for _ in 0..100 {
                scalar
                    .evaluate_into(
                        &scalar_args,
                        &mut scalar_outputs,
                        policy.execution,
                        Some(&memory),
                    )
                    .unwrap();
                canonical
                    .evaluate_into(&args, &mut outputs, policy, &memory)
                    .unwrap();
                outputs.fill(None);
            }
            for round in 0..5 {
                for offset in 0..2 {
                    let program = (round + offset) % 2 == 1;
                    let iterations = 2000;
                    let before = PROBE_ALLOCS.load(Relaxed);
                    let start = std::time::Instant::now();
                    for _ in 0..iterations {
                        if program {
                            canonical
                                .evaluate_into(
                                    std::hint::black_box(&args),
                                    &mut outputs,
                                    policy,
                                    &memory,
                                )
                                .unwrap();
                            assert!(
                                matches!(outputs[last].as_ref().unwrap().data(), mech_core::ValueData::U64(v) if *v == 7 + operations as u64)
                            );
                            outputs.fill(None);
                        } else {
                            scalar
                                .evaluate_into(
                                    std::hint::black_box(&scalar_args),
                                    &mut scalar_outputs,
                                    policy.execution,
                                    Some(&memory),
                                )
                                .unwrap();
                            assert_eq!(
                                scalar_outputs[last],
                                NativeScalarValue::U64(7 + operations as u64)
                            );
                        }
                    }
                    let elapsed = start.elapsed().as_nanos();
                    let allocs = PROBE_ALLOCS.load(Relaxed) - before;
                    println!(
                        "SCALAR_PROBE operations={operations} variant={variant} round={round} path={} ns_per_call={} allocations_per_call={}",
                        if program { "program" } else { "scalar" },
                        elapsed / iterations,
                        allocs / iterations as u64
                    );
                }
            }
        }
    }
}
