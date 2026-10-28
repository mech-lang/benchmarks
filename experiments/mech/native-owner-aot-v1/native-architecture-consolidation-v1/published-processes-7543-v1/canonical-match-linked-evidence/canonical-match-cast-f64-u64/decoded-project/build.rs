use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"0c8b9219ef3262b2569ec41727e769d5d5438d52c902227a8d7a1cb73c0c3642\",\"application.mec\":\"d57479cfe15714b43a4e44c58abbd65f7cb2cb455b9c3f456cdde4185e679d9d\",\"factory-profile.json\":\"58b0cd22f4680bd2c74c1db43dadbb06772a0389f0fcfc9cbe7e17f069480e85\",\"object-identity.bin\":\"9227fc2c0ba7fe53f95e37319c752816db77ca66d5d7c7bfb4a38b3fa0ceb134\",\"program.mecb\":\"8747bf52c7260800153ccaec8151aaa873df35d121a42dddc2a751e3da67cef3\",\"program.o\":\"70490272738e387858526462f02fc162c9dccb750aba7e9f0ec9c189a0a470fe\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"24b99635d895bc1d14a1f8c0ed5b68a7b9f387010122840abf196c068f684b18\"}";
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
