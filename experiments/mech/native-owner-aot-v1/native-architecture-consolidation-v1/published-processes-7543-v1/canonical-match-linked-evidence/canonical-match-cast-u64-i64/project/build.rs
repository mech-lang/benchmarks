use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"1b54835a54b20b51ddb345d5a8f416929e1830a94e6f7c80a517b54f7f9f8926\",\"application.mec\":\"41d5f8cfc49dc2a969ac28ee4649bcd5a62bf1afd2d3b9e29741587985539a96\",\"factory-profile.json\":\"ee2cf68872d8354dd9600599ddc3c74bea5d86de584ddaa75d8754d34a64c8e8\",\"object-identity.bin\":\"89f2e9ced04a195c590760342b3256f90da51c896bbeb674535c5b61019990fa\",\"program.mecb\":\"524d87d4590f26d84f840f890ec2649d5465842fdac66a4d47757adfb494e18c\",\"program.o\":\"cc5f3512612d42a60b0d5b2b64ff39a7f3392a7bf2ae47022939bf72e54731d2\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"6a5329242ed5c827acfe132b555c88ccd168daddc55c1195c911de921b1e808c\"}";
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
