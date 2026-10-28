#[test]
#[ignore = "manual machine-code histogram diagnostic; NOT full secure program timings"]
fn measure_compiled_histogram_kernel_only() {
    let input_path = std::env::var("MECH_HISTOGRAM_KERNEL_INPUT").expect("explicit input required");
    let input = std::fs::read_to_string(input_path).unwrap();
    let mut selected_record = false;
    let mut source = String::new();
    for line in input.lines() {
        if line.starts_with('>') {
            selected_record = line.starts_with(">THREE");
        } else if selected_record {
            source.push_str(line);
        }
    }
    source.make_ascii_uppercase();
    assert_eq!(source.len(), 10_000_000);
    let loan = AsciiSource::borrow(&source).unwrap();
    let selected = Compiled::histogram(false);
    let scalar = Compiled::histogram(true);
    let mut samples = Vec::new();
    for width in [1usize, 2] {
        let expected = reference(&source, width);
        check(&selected, &source, width, &expected);
        check(&scalar, &source, width, &expected);
        for round in 0..7 {
            let variants = if round % 2 == 0 {
                [
                    ("banked", &selected, 4),
                    ("serial", &selected, 1),
                    ("scalar", &scalar, 1),
                ]
            } else {
                [
                    ("scalar", &scalar, 1),
                    ("serial", &selected, 1),
                    ("banked", &selected, 4),
                ]
            };
            for (lowering, code, banks) in variants {
                // Allocation,zeroing,source/oracle preparation and full-bin
                // comparisons are outside these kernel-only intervals.
                let mut bins = vec![0; expected.len() * banks];
                let start = Instant::now();
                let count =
                    code.histogram_count(black_box(&loan), width as u64, black_box(&mut bins));
                let elapsed_ns = start.elapsed().as_nanos();
                assert_eq!(&bins[..expected.len()], expected);
                assert_eq!(count, source.len() as u64 - width as u64 + 1);
                samples.push(serde_json::json!({"round":round,"width":width,"lowering":lowering,"count":count,"all_bins_exact":true,"elapsed_ns":elapsed_ns}));
            }
        }
    }
    eprintln!(
        "HISTOGRAM_KERNEL_DIAGNOSTIC {}",
        serde_json::json!({
            "scope":"Same executable/raw emitted kernel,NOT secured program timing or isolated capability overhead;source prep,allocation,zeroing,host,capabilities,output,accounting and commit excluded",
            "source_bases":source.len(),"samples":samples,"runtime_callbacks_in_emitted_body":0,
            "scratch_layout_changed":true,"object_opt_level":"speed","production_wired":true
        })
    );
}
