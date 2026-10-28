use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"8b67867a61a727da4b626b2099d08a4f3cc30f42907298b8d7694b8d79928317\",\"application.mec\":\"5de67c7f2d411373dd7e3f826398fd1ac391156b5bd0bc2569e04d91f0e20c22\",\"factory-profile.json\":\"c2a37201ffdbb7577a6dba55db93b0867be130a9805048d8c42c9395a420880a\",\"object-identity.bin\":\"2817067bc637369b52fb70943800a8b8b8a0cd2127545d6f6a260de9d8c09ed7\",\"program.mecb\":\"0007424a213d9841de84b28e18cfb7f5f813c380ed2c822ce7aed62822e7abbf\",\"program.o\":\"a4ff401a1c3eed3fb54d1c132c837f679ad29e9d722ac49962288cacb7e8a51e\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"d76c99708e4ea63ebfc73b2e53c57b5ab4f2d572818fb9593b44e2a3dbc3267f\"}";
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
