use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"6b5e6f603ea0e5d76d95be3310f076ab3ed267df57d68196a42950a5c93afdb1\",\"application.mec\":\"9965de10a371f49e345ba7a4e2211cfd41786ae19a33cc539cef1b3cd41c178e\",\"factory-profile.json\":\"5c9ecad8eef09428fb43e8bbd9138bdca4786959d216f547fc000bf2d9b17380\",\"object-identity.bin\":\"0e0012662dd6b51c0d7fb473df5ee7f9cba617fcb762f4f26f397a693f38e34c\",\"program.mecb\":\"4e44b586a8d1bc4410dceb16ca418c9c7df7cea12f94cc4de010ef3293a94898\",\"program.o\":\"e7d0a795a436d348681136c18311ae26cc22cb963c841678509fddd4354ae86c\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"8e7bad490386291967eb17bf35a19c15833779d2bcf09f3aafe0a02fc8957ad4\"}";
fn digest(bytes: &[u8]) -> String {
    Sha256::digest(bytes)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}
fn main() {
    assert_eq!(
        std::env::var("HOST").unwrap(),
        std::env::var("TARGET").unwrap(),
        "canonical native object is host-only"
    );
    let root = PathBuf::from(std::env::var_os("CARGO_MANIFEST_DIR").unwrap());
    let expected: BTreeMap<String, String> = serde_json::from_str(EXPECTED).unwrap();
    let manifest_bytes = fs::read(root.join("linked-manifest.json")).unwrap();
    let manifest: serde_json::Value = serde_json::from_slice(&manifest_bytes).unwrap();
    assert_eq!(manifest["schema"], "mech.canonical-linked-application.v1");
    let mut pins: BTreeMap<String, String> =
        serde_json::from_value(manifest["pins"].clone()).unwrap();
    let script = pins.remove("build.rs").expect("build script pin");
    assert_eq!(
        digest(&fs::read(root.join("build.rs")).unwrap()),
        script,
        "build script changed"
    );
    assert_eq!(pins, expected, "manifest generated-input pins changed");
    for (name, hash) in expected {
        assert_eq!(
            digest(&fs::read(root.join(&name)).unwrap()),
            hash,
            "changed generated input {name}"
        );
        println!("cargo:rerun-if-changed={name}");
    }
    println!("cargo:rerun-if-changed=linked-manifest.json");
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rustc-link-arg={}", root.join("program.o").display());
}
