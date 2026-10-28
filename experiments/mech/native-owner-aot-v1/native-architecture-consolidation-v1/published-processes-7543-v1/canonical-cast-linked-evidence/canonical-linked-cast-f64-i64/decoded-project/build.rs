use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"29f04410908ac5fc625a5ef662c9795ea002083b4d57a83621fc2ebe861a1c52\",\"application.mec\":\"be51a1370c7f39015662bbc8b656745a158aff19cf8aa34570c43b1e55c9a7ee\",\"factory-profile.json\":\"dde53b11f71a7e5764db8155d1fc2f95094c617c8e0be0f30b54bf450216720d\",\"object-identity.bin\":\"3bbd7f0475325f396a5772accd8a5b5240dff24554b1bc337ebde4dc89cfb716\",\"program.mecb\":\"7693081ba21c784f7dc1aa608c70a21d156b9447ebca6b615025a46229c20f6c\",\"program.o\":\"b0c5a9e59e698b8867168fab9ddffaeec1237bc5dda78a8cd77ffb2978efb4fa\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"93449bcfa77b732356d00c990279a2e644ad9b2ec29fea574605f630e6a3f862\"}";
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
