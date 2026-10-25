//! Explicit orchestration of already-qualified current candidate binaries.
use mech_canonical_hosted_runner::{Profile, Qualification};
use std::{fs, path::Path};

fn main() {
    let args = std::env::args_os().skip(1).collect::<Vec<_>>();
    assert!(
        args.len() == 7,
        "usage: runner production|comparison RESULTS_JSON EVIDENCE_DIR CANDIDATE_COMMIT RUNNER_COMMIT SOURCE_SHA256 SMALL_LAUNCH_JSON"
    );
    let comparison = match args[0].to_str() {
        Some("production") => false,
        Some("comparison") => true,
        _ => panic!("expected production or comparison"),
    };
    let results: Vec<serde_json::Value> =
        serde_json::from_slice(&fs::read(&args[1]).unwrap()).unwrap();
    let evidence = Path::new(&args[2]);
    assert!(
        evidence.is_absolute() && !evidence.exists(),
        "fresh absolute evidence directory required"
    );
    fs::create_dir_all(evidence).unwrap();
    let context = Qualification {
        candidate_mech_revision: args[3].to_str().unwrap().into(),
        runner_revision: args[4].to_str().unwrap().into(),
        source_sha256: args[5].to_str().unwrap().into(),
        small_launch: serde_json::from_slice(&fs::read(&args[6]).unwrap()).unwrap(),
    };
    let result = if comparison {
        mech_canonical_hosted_runner::run_comparison(Profile::Release, &context, evidence, &results)
    } else {
        mech_canonical_hosted_runner::run(Profile::Release, &context, evidence, &results)
    };
    assert!(
        !result.is_null(),
        "explicit single or staged configuration environment is required"
    );
}
