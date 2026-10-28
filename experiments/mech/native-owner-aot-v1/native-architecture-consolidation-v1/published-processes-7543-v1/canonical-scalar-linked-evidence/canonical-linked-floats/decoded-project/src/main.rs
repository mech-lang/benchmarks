//! Build-owned symbols and statically selected compiled launcher.
use std::ffi::c_void;
use mech_gpu::native_artifact::{NATIVE_LINK_IDENTITY_BYTES, launch::{BuildOwnedScalarBinding, run_scalar_application}};
unsafe extern "C" {
    #[link_name = "mech_canonical_scalar_entry_v1"]
    fn linked_entry(frame: *mut c_void) -> u64;
    #[link_name = "mech_canonical_scalar_identity_v1_4e5c394f421195fa1980b009a4bf9e5a90ebe0ada18f019ecc87b0771f9921a9"]
    static LINKED_IDENTITY: [u8; NATIVE_LINK_IDENTITY_BYTES];
}
fn catalog() -> Result<mech_core::FunctionCatalog, String> {
    let mut builder = mech_core::FunctionCatalogBuilder::new();
mech_engine::linked_factories::COMPARE_EQ.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_COMPARE_GT.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_COMPARE_GTE.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_COMPARE_LT.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_COMPARE_LTE.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::COMPARE_NEQ.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_MATH_ADD.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_MATH_DIV.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_MATH_MUL.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_MATH_NEG.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_MATH_SQRT.install(&mut builder).map_err(|error| format!("{error:?}"))?;
mech_engine::linked_factories::NUMERIC_MATH_SUB.install(&mut builder).map_err(|error| format!("{error:?}"))?;
    builder.build().map_err(|error| format!("{error:?}"))
}
fn main() {
    // SAFETY: build.rs verifies the unchanged bytecode/Object/generated-input
    // pins. These process-lifetime symbols come from that SAME checked Object.
    let binding = unsafe { BuildOwnedScalarBinding::from_build_owned_entry(
        include_bytes!("../program.mecb"), "6b9ad60022091d3e0ecaee44e1be46944820db22ce928012833ee0127012e236",
        &LINKED_IDENTITY, linked_entry, catalog,
    ) };
    if let Err(error) = run_scalar_application(binding, std::env::args_os().skip(1).collect()) {
        eprintln!("{error}"); std::process::exit(1);
    }
}
