//! Maintained full-input qualification and serial performance orchestration.
use serde_json::Value;
#[cfg(test)]
use serde_json::json;
use sha2::{Digest, Sha256};
#[path = "canonical_hosted_full.rs"]
mod full;
pub use full::{comparison_control, run, run_comparison};
pub mod profile {
    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum Profile {
        Debug,
        Release,
    }
    impl Profile {
        pub fn release(self) -> bool {
            self == Self::Release
        }
    }
}
pub use profile::Profile;
/// Pins supplied by the candidate build harness, never inferred from program output.
pub struct Qualification {
    pub runner_revision: String,
    pub candidate_mech_revision: String,
    pub source_sha256: String,
    pub small_launch: Value,
}
impl Qualification {
    fn validate(&self, results: &[Value]) -> Result<(), String> {
        fn hex(value: &str, width: usize) -> bool {
            value.len() == width
                && value
                    .bytes()
                    .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        }
        if !hex(&self.runner_revision, 40)
            || !hex(&self.candidate_mech_revision, 40)
            || !hex(&self.source_sha256, 64)
        {
            return Err(
                "qualification requires immutable runner/candidate commits and source SHA256"
                    .into(),
            );
        }
        if results.len() != 2
            || results
                .iter()
                .any(|row| row["source_sha256"] != self.source_sha256)
        {
            return Err("qualified candidate source differs from runner input".into());
        }
        Ok(())
    }
}
fn hash(bytes: &[u8]) -> String {
    Sha256::digest(bytes)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}
#[cfg(test)]
fn launch() -> Value {
    json!({
        "grants": [
            {"target":"cli/stdin","operations":["read"],"paths":["text"]},
            {"target":"cli/stdout","operations":["write"],"paths":["text"]}
        ],
        "max_ports":16,
        "input_text_bytes":1048576,
        "output_text_bytes":1048576,
        "memory_bytes":268435456,
        "work":1000000000,
        "transport_bytes":16777216,
        "native_stack_bytes":1048576,
        "library": {
            "output_elements":1000000, "output_bytes":134217728,
            "temporary_bytes":134217728, "cloned_bytes":134217728,
            "retained_nodes":1000000, "compute_work":134217728,
            "comparison_work":1000000
        }
    })
}
#[cfg(test)]
fn test_context() -> Qualification {
    Qualification {
        runner_revision: "a".repeat(40),
        candidate_mech_revision: "b".repeat(40),
        source_sha256: hash(b"test source"),
        small_launch: launch(),
    }
}

#[test]
fn runner_and_candidate_pins_are_required_before_dispatch() {
    let mut context = test_context();
    let rows = std::array::from_fn::<_, 2, _>(|_| json!({"source_sha256":context.source_sha256}));
    assert!(context.validate(&rows).is_ok());
    context.runner_revision = "main".into();
    assert!(context.validate(&rows).is_err());
    context = test_context();
    context.candidate_mech_revision = "b".repeat(39);
    assert!(context.validate(&rows).is_err());
    context = test_context();
    let mut different = rows.clone();
    different[1]["source_sha256"] = json!("c".repeat(64));
    assert!(context.validate(&different).is_err());
    assert!(context.validate(&rows[..1]).is_err());
}
