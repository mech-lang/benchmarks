use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"a981dfa27587011bf506edef3778f1f880ac8fb54aac4e7636e01d0df94c501a\",\"application.mec\":\"6f200fa8fa6ba169a5b38c12697a6b250044dc4d72f0ef6966408cdb665e0360\",\"factory-profile.json\":\"959cbe708dbf65e48666411b97ffb18773b90cd18f90bfe8ca78bfe5b2ef3ca4\",\"object-identity.bin\":\"f27bb31b1ea5539640cb8d231eccf0c2e496a53f60b4bbd02233609a1ea0c8d6\",\"program.mecb\":\"f0c4cbd0f658429cab72dc5aca78b1523977f0e82c358e343f752174268a5212\",\"program.o\":\"ea612c0e9d54b615b83a83bd7679d4b8a6cb517d6cfc45a890e362077c4e93dc\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"387996f52b5e9b8ae83484075a8ca7db63d72f01e8f8c2262b15243cc6508148\"}";
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
    assert_eq!(manifest["schema"], "mech.canonical-linked-match-application.v1");
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
