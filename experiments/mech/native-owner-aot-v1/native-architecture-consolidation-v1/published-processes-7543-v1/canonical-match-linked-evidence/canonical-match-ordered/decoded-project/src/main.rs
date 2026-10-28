//! Build-owned symbols and statically selected compiled launcher.
use std::ffi::c_void;
use mech_gpu::native_artifact::{NATIVE_MATCH_LINK_IDENTITY_BYTES, launch::{BuildOwnedMatchBinding, run_match_application}};
unsafe extern "C" {
    #[link_name = "mech_canonical_scalar_match_entry_v1"]
    fn linked_entry(frame: *mut c_void) -> u64;
    #[link_name = "mech_canonical_scalar_match_identity_v1_103311393de7f11e12fd75261334a771eb174abd4cd6cd3c9952ff5ca31ee167"]
    static LINKED_IDENTITY: [u8; NATIVE_MATCH_LINK_IDENTITY_BYTES];
}
fn catalog() -> Result<mech_core::FunctionCatalog, String> {
    let mut builder = mech_core::FunctionCatalogBuilder::new();
mech_engine::linked_factories::NUMERIC_MATH_ADD.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_MATH_DIV.install(&mut builder).map_err(|error| format!("{error:?}"))?;
    builder.build().map_err(|error| format!("{error:?}"))
}
fn main() {
    // SAFETY: build.rs verifies the unchanged bytecode/Object/generated-input
    // pins. These process-lifetime symbols come from that SAME checked Object.
    let binding = unsafe { BuildOwnedMatchBinding::from_build_owned_entry(
        include_bytes!("../program.mecb"), "170e1f543bcc83f8751e87adde19ff0a916dbdc1ce24934dde569fd435f339a7",
        &LINKED_IDENTITY, linked_entry, catalog,
    ) };
    if let Err(error) = run_match_application(binding, std::env::args_os().skip(1).collect()) {
        eprintln!("{error}"); std::process::exit(1);
    }
}
