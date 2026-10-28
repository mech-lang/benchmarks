//! Build-owned symbols and statically selected compiled launcher.
use std::ffi::c_void;
use mech_gpu::native_artifact::{NATIVE_LINK_IDENTITY_BYTES, launch::{BuildOwnedScalarBinding, run_scalar_application}};
unsafe extern "C" {
    #[link_name = "mech_canonical_scalar_entry_v1"]
    fn linked_entry(frame: *mut c_void) -> u64;
    #[link_name = "mech_canonical_scalar_identity_v1_c05907c9bd10529e6baefed8e25cb5d78e83ed6d80f064a1157fc428717de6fa"]
    static LINKED_IDENTITY: [u8; NATIVE_LINK_IDENTITY_BYTES];
}
fn catalog() -> Result<mech_core::FunctionCatalog, String> {
    let mut builder = mech_core::FunctionCatalogBuilder::new();
mech_engine::linked_factories::NUMERIC_LOGIC_NOT.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_MATH_ADD.install(&mut builder).map_err(|error| format!("{error:?}"))?;
    builder.build().map_err(|error| format!("{error:?}"))
}
fn main() {
    // SAFETY: build.rs verifies the unchanged bytecode/Object/generated-input
    // pins. These process-lifetime symbols come from that SAME checked Object.
    let binding = unsafe { BuildOwnedScalarBinding::from_build_owned_entry(
        include_bytes!("../program.mecb"), "0eccf9ca8dfe2cec19f918a934430524350556fad31c25ac61a5b3c515ccd7fe",
        &LINKED_IDENTITY, linked_entry, catalog,
    ) };
    if let Err(error) = run_scalar_application(binding, std::env::args_os().skip(1).collect()) {
        eprintln!("{error}"); std::process::exit(1);
    }
}
