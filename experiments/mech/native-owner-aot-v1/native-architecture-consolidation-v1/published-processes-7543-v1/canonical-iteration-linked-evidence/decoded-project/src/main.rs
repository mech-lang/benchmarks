//! Build-owned symbols and statically selected compiled launcher.
use std::ffi::c_void;
use mech_gpu::native_artifact::{NATIVE_ITERATION_LINK_IDENTITY_BYTES, launch::{BuildOwnedIterationBinding, run_iteration_application}};
unsafe extern "C" {
    #[link_name = "mech_canonical_scalar_iteration_entry_v1"]
    fn linked_entry(frame: *mut c_void) -> u64;
    #[link_name = "mech_canonical_scalar_iteration_identity_v1_12c1077dab5f2a5814e153ddcaef54cc40115b78ccde5c43f72f057cef03e0d4"]
    static LINKED_IDENTITY: [u8; NATIVE_ITERATION_LINK_IDENTITY_BYTES];
}
fn catalog() -> Result<mech_core::FunctionCatalog, String> {
    let mut builder = mech_core::FunctionCatalogBuilder::new();
mech_engine::linked_factories::NUMERIC_MATH_ADD.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_MATH_MUL.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_MATH_SUB.install(&mut builder).map_err(|error| format!("{error:?}"))?;
    builder.build().map_err(|error| format!("{error:?}"))
}
fn main() {
    // SAFETY: build.rs verifies the unchanged bytecode/Object/generated-input
    // pins. These process-lifetime symbols come from that SAME checked Object.
    let binding = unsafe { BuildOwnedIterationBinding::from_build_owned_entry(
        include_bytes!("../program.mecb"), "bde9ffb5d62d1c486f48dbab786fbff23caa8d8b4eec093b2442d62d4f9c22b9",
        &LINKED_IDENTITY, linked_entry, catalog,
    ) };
    if let Err(error) = run_iteration_application(binding, std::env::args_os().skip(1).collect()) {
        eprintln!("{error}"); std::process::exit(1);
    }
}
