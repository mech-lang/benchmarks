//! Same-Object image/symbol binding and compiled launcher dispatch.
use std::ffi::c_void;
use mech_gpu::native_artifact::{NATIVE_PROGRAM_LINK_IDENTITY_BYTES, launch::{BuildOwnedHostedBinding, run_hosted_program_application}};
unsafe extern "C" {
    #[link_name = "mech_canonical_program_entry_v1"]
    fn linked_entry(frame: *mut c_void) -> u64;
    #[link_name = "mech_canonical_program_identity_v1_0db36b537bf3d3a05359a7f55b38939156693531893d16f11782a2957269103c"]
    static LINKED_IDENTITY: [u8; NATIVE_PROGRAM_LINK_IDENTITY_BYTES];
}
fn catalog() -> Result<mech_core::FunctionCatalog, String> {
    let mut builder = mech_core::FunctionCatalogBuilder::new();

    builder.build().map_err(|error| format!("{error:?}"))
}
fn main() {
    // SAFETY: build.rs verifies the unchanged Object/images and all generated
    // inputs. Entry, identity and images belong to that SAME checked build.
    let binding = unsafe { BuildOwnedHostedBinding::from_build_owned_image(
        include_bytes!("../native-descriptor.bin"), include_bytes!("../native-resources.json"),
        &LINKED_IDENTITY, linked_entry, catalog, "canonical-artifact-program-object-secured-cli",
    ) };
    if let Err(error) = run_hosted_program_application(binding, std::env::args_os().skip(1)) {
        eprintln!("{error}"); std::process::exit(1);
    }
}
