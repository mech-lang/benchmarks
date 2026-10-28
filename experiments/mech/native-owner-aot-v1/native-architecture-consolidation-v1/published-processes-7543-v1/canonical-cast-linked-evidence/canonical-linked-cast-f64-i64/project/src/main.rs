//! Build-owned symbols and statically selected compiled launcher.
use std::ffi::c_void;
use mech_gpu::native_artifact::{NATIVE_LINK_IDENTITY_BYTES, launch::{BuildOwnedScalarBinding, run_scalar_application}};
unsafe extern "C" {
    #[link_name = "mech_canonical_scalar_entry_v1"]
    fn linked_entry(frame: *mut c_void) -> u64;
    #[link_name = "mech_canonical_scalar_identity_v1_2bf85dafea16cace5a0aa490c204f1bf3e54646bc555bc7064ad591d4a7a97f5"]
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
        include_bytes!("../program.mecb"), "7693081ba21c784f7dc1aa608c70a21d156b9447ebca6b615025a46229c20f6c",
        &LINKED_IDENTITY, linked_entry, catalog,
    ) };
    if let Err(error) = run_scalar_application(binding, std::env::args_os().skip(1).collect()) {
        eprintln!("{error}"); std::process::exit(1);
    }
}
