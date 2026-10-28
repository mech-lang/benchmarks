use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"fc544ddbdd276c3a7ea5cc7835fe15cab12a1ce3a68964cc47862896b80fe21e\",\"application.mec\":\"cae3fb5b720ee0dab792da5c20664e7d05da023e9d8057cf51dab9da47c85437\",\"factory-profile.json\":\"17a78600dde2611516135bb3c06fa201872c44c62ff26998f8da67df5eb09031\",\"object-identity.bin\":\"54e3e4b75919b99022700498aa03196043316773a0a656d44e2d9343170f27bd\",\"program.mecb\":\"c65a6b4cc5a43552428d06f9d98ebc53559f0d301cdb012c3cfa920d47cf7718\",\"program.o\":\"023038786c78489f4832c0396c53dd3e73692e6ac26555a4ef78c800ea7e370e\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"6c5e1fad63af34f3e76b0650cf8cd588c53ca33f6d3076c635e75ce9af87efd5\"}";
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
