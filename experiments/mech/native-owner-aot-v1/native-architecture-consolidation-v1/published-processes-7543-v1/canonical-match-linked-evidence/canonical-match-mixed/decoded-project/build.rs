use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"5f33c534db3d80eda9473cfa0ed8632408b992ec1eb56dc80af6a37cce88bc96\",\"application.mec\":\"2bf5ce5af7dc275c0999bd02b6a32cc61ac3aa57e5ad3983f374279956101f64\",\"factory-profile.json\":\"e7fe4cbbb723e3e84abf5716f497417e6a19bb10b83420165c9dd290916c06e8\",\"object-identity.bin\":\"8192b5d49dbe23fadef7bc2bc41a349a89606bb682d42d9f99ce7063c5ad0476\",\"program.mecb\":\"b98c55a52314f6b6a273f0e12cfa2ac9a7d8dafb3cd6f383a7f895bf6cf1e3af\",\"program.o\":\"92b0766ad81aa088dd4ed78a696dc29182a97d9a0c51654310cfc1d829839ca0\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"680ee2d284feaf0a1218be83c8614a8258929322ccbfaa58060c672dea19af94\"}";
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
