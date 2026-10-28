use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"5857bca8b1d7a0d060e147ee2949f0a76c953664606592805f963a5eb692705c\",\"application.mec\":\"4090e03e689c89ba41823812bd6abebaf12073bb62a16b1f097ca3f89247c98b\",\"factory-profile.json\":\"06b21f7c13874d7ede7a9020668b50ad9d4f60b1db6a3bb0afb4eae987fdad48\",\"native-descriptor.bin\":\"12182a332827d85a6132cdf641d1437e29bb85947fbe0a3dccba5ab33a7d1b4d\",\"native-descriptor.json\":\"35aee39e6be4931a68fb3705aba95a94395f3cc9474887d95c0784f60824a2e5\",\"object-identity.bin\":\"5b8d38572c52e3b69b4663f2c2ab3c83678dee59c533f17af22c3390b30a971b\",\"program.mecb\":\"485392f0dcffc3a19869994da56e8d80fa9a1995e6afad0aa70b8f571d0c1868\",\"program.o\":\"c3386ef8da624359aa069b2a8d9f3080dc508983d6e3f58f52659d228332aab5\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"0682c13303b1d2c080c92b438d3547075c49427f63dbfa7d63fa33f9627c3888\"}";
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
    assert_eq!(manifest["schema"], "mech.canonical-linked-program-application.v1");
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
