//! Build-owned symbols and statically selected compiled launcher.
use std::ffi::c_void;
use mech_gpu::native_artifact::{NATIVE_MATCH_LINK_IDENTITY_BYTES, launch::{BuildOwnedMatchBinding, run_match_application}};
unsafe extern "C" {
    #[link_name = "mech_canonical_scalar_match_entry_v1"]
    fn linked_entry(frame: *mut c_void) -> u64;
    #[link_name = "mech_canonical_scalar_match_identity_v1_a3e439d59cb27e3c6630f64b6924d7db01a1beadba0e3764fb57d3de757fc06a"]
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
        include_bytes!("../program.mecb"), "524d87d4590f26d84f840f890ec2649d5465842fdac66a4d47757adfb494e18c",
        &LINKED_IDENTITY, linked_entry, catalog,
    ) };
    if let Err(error) = run_match_application(binding, std::env::args_os().skip(1).collect()) {
        eprintln!("{error}"); std::process::exit(1);
    }
}
