//! Same-Object image/symbol binding and compiled launcher dispatch.
use std::ffi::c_void;
use mech_gpu::native_artifact::{NATIVE_PROGRAM_LINK_IDENTITY_BYTES, launch::{BuildOwnedProgramBinding, run_program_application}};
unsafe extern "C" {
    #[link_name = "mech_canonical_program_entry_v1"]
    fn linked_entry(frame: *mut c_void) -> u64;
    #[link_name = "mech_canonical_program_identity_v1_d07fd6584d69a5494a5e7ce8680d2dcf7c27984faa3509fd0b73aa43aca83c45"]
    static LINKED_IDENTITY: [u8; NATIVE_PROGRAM_LINK_IDENTITY_BYTES];
}
fn catalog() -> Result<mech_core::FunctionCatalog, String> {
    let mut builder = mech_core::FunctionCatalogBuilder::new();
mech_engine::linked_factories::MAP_HISTOGRAM.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::MAP_KEYS.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::MAP_VALUES.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMBER_FORMAT.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::SEQUENCE_LENGTH.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::TEXT_JOIN.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::TEXT_LINES.install(&mut builder).map_err(|error| format!("{error:?}"))?;
    builder.build().map_err(|error| format!("{error:?}"))
}
fn main() {
    // SAFETY: build.rs verifies the unchanged Object/images and all generated
    // inputs. Entry, identity and images belong to that SAME checked build.
    let binding = unsafe { BuildOwnedProgramBinding::from_build_owned_image(
        include_bytes!("../native-descriptor.bin"),
        &LINKED_IDENTITY, linked_entry, catalog,
    ) };
    if let Err(error) = run_program_application(binding, std::env::args_os().skip(1).collect()) {
        eprintln!("{error}"); std::process::exit(1);
    }
}
