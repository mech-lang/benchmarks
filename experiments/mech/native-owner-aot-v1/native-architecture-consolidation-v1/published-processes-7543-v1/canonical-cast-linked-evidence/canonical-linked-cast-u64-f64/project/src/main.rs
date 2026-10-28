//! Build-owned symbols and statically selected compiled launcher.
use std::ffi::c_void;
use mech_gpu::native_artifact::{NATIVE_LINK_IDENTITY_BYTES, launch::{BuildOwnedScalarBinding, run_scalar_application}};
unsafe extern "C" {
    #[link_name = "mech_canonical_scalar_entry_v1"]
    fn linked_entry(frame: *mut c_void) -> u64;
    #[link_name = "mech_canonical_scalar_identity_v1_c215c593a085310bb8143b7ca4704bd8c5c03d9fd7cef2d114f300f7e1eefdda"]
    static LINKED_IDENTITY: [u8; NATIVE_LINK_IDENTITY_BYTES];
}
fn catalog() -> Result<mech_core::FunctionCatalog, String> {
    let mut builder = mech_core::FunctionCatalogBuilder::new();
mech_engine::linked_factories::CONVERT_KIND.install(&mut builder).map_err(|error| format!("{error:?}"))?;
    builder.build().map_err(|error| format!("{error:?}"))
}
fn main() {
    // SAFETY: build.rs verifies the unchanged bytecode/Object/generated-input
    // pins. These process-lifetime symbols come from that SAME checked Object.
    let binding = unsafe { BuildOwnedScalarBinding::from_build_owned_entry(
        include_bytes!("../program.mecb"), "1933f71dffb7a5c624a0ae58561110e0eaa8bd5b03bf9d522f412e49f40715a5",
        &LINKED_IDENTITY, linked_entry, catalog,
    ) };
    if let Err(error) = run_scalar_application(binding, std::env::args_os().skip(1).collect()) {
        eprintln!("{error}"); std::process::exit(1);
    }
}
