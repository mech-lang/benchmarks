#[test]
#[ignore = "manual machine-code kernel diagnostic; NOT full secure program timings"]
fn measure_compiled_window_query_kernel_only() {
    let input_path =
        std::env::var("MECH_WINDOW_KERNEL_INPUT").expect("explicit diagnostic input required");
    let oracle_path =
        std::env::var("MECH_WINDOW_KERNEL_ORACLE").expect("explicit exact oracle required");
    let input = std::fs::read_to_string(input_path).unwrap();
    let oracle = std::fs::read_to_string(oracle_path).unwrap();
    // Diagnostic setup ONLY. This is deliberately outside every timed call;
    // it is NOT claimed to measure FASTA selection/case conversion, hosting,
    // accounting, snapshot ownership, output or round/commit overhead.
    let mut selected = false;
    let mut source = String::new();
    for line in input.lines() {
        if line.starts_with('>') {
            selected = line.starts_with(">THREE");
        } else if selected {
            source.push_str(line);
        }
    }
    source.make_ascii_uppercase();
    assert_eq!(source.len(), 10_000_000);
    let compiled = Compiled::new();
    let scalar = Compiled::scalar();
    let source_loan = AsciiSource::borrow(&source).unwrap();
    let queries = [
        "GGT",
        "GGTA",
        "GGTATT",
        "GGTATTTTAATT",
        "GGTATTTTAATTTATAGT",
    ];
    let expected = queries.map(|query| {
        oracle
            .lines()
            .find_map(|line| {
                let (count, label) = line.split_once('\t')?;
                (label == query).then(|| count.parse::<u64>().unwrap())
            })
            .unwrap()
    });
    for (query, wanted) in queries.iter().zip(expected) {
        assert_eq!(
            compiled.count(&source_loan, query.len() as u64, query),
            wanted
        );
        assert_eq!(
            scalar.count(&source_loan, query.len() as u64, query),
            wanted
        );
    }
    let mut rows = Vec::new();
    for round in 0..7 {
        for (index, query) in queries.iter().enumerate() {
            let variants = if round % 2 == 0 {
                [("selected", &compiled), ("scalar", &scalar)]
            } else {
                [("scalar", &scalar), ("selected", &compiled)]
            };
            for (lowering, code) in variants {
                let start = Instant::now();
                let count = code.count(
                    black_box(&source_loan),
                    query.len() as u64,
                    black_box(query),
                );
                let elapsed_ns = start.elapsed().as_nanos();
                assert_eq!(count, expected[index]);
                rows.push(serde_json::json!({"round":round,"query":query,"lowering":lowering,"count":count,"elapsed_ns":elapsed_ns}));
            }
        }
    }
    eprintln!(
        "WINDOW_KERNEL_DIAGNOSTIC {}",
        serde_json::json!({
        "scope":"isolated shared-emitter kernel; ASCII loan validated once outside samples; NOT secure end-to-end performance or recovered-original-body qualification",
        "source_bases":source.len(),"object_opt_level":"speed","samples":rows,
        "comparison":"same executable and input; target-selected lowering versus scalar; alternating order; excludes host/capabilities and is NOT full-program timing",
        "runtime_callbacks_in_emitted_body":0,"production_wired":true})
    );
}
