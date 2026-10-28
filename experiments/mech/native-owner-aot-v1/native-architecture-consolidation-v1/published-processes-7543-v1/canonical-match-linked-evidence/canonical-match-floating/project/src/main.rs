//! Build-owned symbols and statically selected compiled launcher.
use std::ffi::c_void;
use mech_gpu::native_artifact::{NATIVE_MATCH_LINK_IDENTITY_BYTES, launch::{BuildOwnedMatchBinding, run_match_application}};
unsafe extern "C" {
    #[link_name = "mech_canonical_scalar_match_entry_v1"]
    fn linked_entry(frame: *mut c_void) -> u64;
    #[link_name = "mech_canonical_scalar_match_identity_v1_4739ad1b8c94abe82b0820a4c4d0c3ac724387798d24284cc0e30eb0ddef58c4"]
    static LINKED_IDENTITY: [u8; NATIVE_MATCH_LINK_IDENTITY_BYTES];
}
fn catalog() -> Result<mech_core::FunctionCatalog, String> {
    let mut builder = mech_core::FunctionCatalogBuilder::new();

    builder.build().map_err(|error| format!("{error:?}"))
}
fn main() {
    // SAFETY: build.rs verifies the unchanged bytecode/Object/generated-input
    // pins. These process-lifetime symbols come from that SAME checked Object.
    let binding = unsafe { BuildOwnedMatchBinding::from_build_owned_entry(
        include_bytes!("../program.mecb"), "c65a6b4cc5a43552428d06f9d98ebc53559f0d301cdb012c3cfa920d47cf7718",
        &LINKED_IDENTITY, linked_entry, catalog,
    ) };
    if let Err(error) = run_match_application(binding, std::env::args_os().skip(1).collect()) {
        eprintln!("{error}"); std::process::exit(1);
    }
}
