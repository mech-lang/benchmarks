#[test]
#[ignore = "manual canonical window-region compiler diagnostic; not a benchmark"]
fn inspect_complete_window_query_compiler_region() {
    for (variant, artifact) in artifacts(QUERY).0.iter().enumerate() {
        let jit = JitProgramArtifact::compile(artifact, &mech_stdlib::source_catalog()).unwrap();
        let plan = jit.descriptor().plan();
        let collections = plan
            .collections()
            .iter()
            .filter(|collection| {
                collection.string_span_projection().is_some()
                    && matches!(
                        collection.result(),
                        NativeCollectionResult::GuardedHistogramQuery(_)
                    )
            })
            .collect::<Vec<_>>();
        assert_eq!(collections.len(), 1);
        eprintln!("WINDOW_REGION variant={variant} entry={}", plan.entry());
        eprintln!("COLLECTION {:#?}", collections[0]);
        eprintln!("ITERATIONS {:#?}", plan.iterations());
        for constant in plan.constants() {
            eprintln!("CONSTANT {constant:?}");
        }
        for (index, block) in plan.blocks().iter().enumerate() {
            eprintln!(
                "BLOCK {index} iteration={:?} action={:?} terminator={:?}",
                block.iteration(),
                block.action(),
                block.terminator()
            );
        }
    }
}
