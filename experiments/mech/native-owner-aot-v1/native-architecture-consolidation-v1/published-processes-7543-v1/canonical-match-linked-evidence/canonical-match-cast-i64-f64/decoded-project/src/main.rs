//! Build-owned symbols and statically selected compiled launcher.
use std::ffi::c_void;
use mech_gpu::native_artifact::{NATIVE_MATCH_LINK_IDENTITY_BYTES, launch::{BuildOwnedMatchBinding, run_match_application}};
unsafe extern "C" {
    #[link_name = "mech_canonical_scalar_match_entry_v1"]
    fn linked_entry(frame: *mut c_void) -> u64;
    #[link_name = "mech_canonical_scalar_match_identity_v1_b623b2d869aa466872c5bfae5a3ad94115885254fac15d253d7f9c3485cbab3b"]
    static LINKED_IDENTITY: [u8; NATIVE_MATCH_LINK_IDENTITY_BYTES];
}
fn catalog() -> Result<mech_core::FunctionCatalog, String> {
    let mut builder = mech_core::FunctionCatalogBuilder::new();
mech_engine::linked_factories::CONVERT_KIND.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_MATH_ADD.install(&mut builder).map_err(|error| format!("{error:?}"))?;
    builder.build().map_err(|error| format!("{error:?}"))
}
fn main() {
    // SAFETY: build.rs verifies the unchanged bytecode/Object/generated-input
    // pins. These process-lifetime symbols come from that SAME checked Object.
    let binding = unsafe { BuildOwnedMatchBinding::from_build_owned_entry(
        include_bytes!("../program.mecb"), "4aaeb69d0023621a6ec05146c6ddad21a767ee4ecebc4129f68609ff5145c814",
        &LINKED_IDENTITY, linked_entry, catalog,
    ) };
    if let Err(error) = run_match_application(binding, std::env::args_os().skip(1).collect()) {
        eprintln!("{error}"); std::process::exit(1);
    }
}
