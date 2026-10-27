use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"a8c0fc97c7950d80534fbcb849febd39c964f96f12f87a5355d825953fb5ce4e\",\"application.mec\":\"fcf8a8653fd3dd8efd5e086def186ea9ca99e45a0124cbb25121137a130e4c47\",\"factory-profile.json\":\"ee2cf68872d8354dd9600599ddc3c74bea5d86de584ddaa75d8754d34a64c8e8\",\"object-identity.bin\":\"92b112f298623a87adf08a7773c1162bb23a247f0bc35fca68547c66ed320524\",\"program.mecb\":\"af2880ed9a606a76a0b332ef88ff8542f46ec93a42c3d02456df177af0076121\",\"program.o\":\"e7752975602adea3894ea6ae706bc56037fe1aedd778eccb6fd5b77b8ae1ccf5\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"2fbe6be9883965b30139c61f4bc9d7f5af232751b89197ccbdf1647a6a5b8123\"}";
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
