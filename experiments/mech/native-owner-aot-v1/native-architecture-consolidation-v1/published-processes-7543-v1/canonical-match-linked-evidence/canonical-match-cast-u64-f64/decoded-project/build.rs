use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"2d325f4d3208cbb98b68a82b254ff694888ca110304e03519bdeed4332fd3372\",\"application.mec\":\"c8bc12311c2d948cfb4fdc961f7f0d159fc044f7200cfc6c712b3c580db925c0\",\"factory-profile.json\":\"58b0cd22f4680bd2c74c1db43dadbb06772a0389f0fcfc9cbe7e17f069480e85\",\"object-identity.bin\":\"c6f4ed230f4919799f5c839c0b196ceef6a4fd5d5409ebad373be2ab80272467\",\"program.mecb\":\"d2edb8173b477b2d8364c508d2338ed82f51b11604ff4e59d987938cdfb035d4\",\"program.o\":\"cf76483e3b3f85dafcc3585aab4445226fca4ee870bb5b8235080784786be8e1\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"c71c12fbdb6a33fd99835d55e0e18bc23d53caf0dcd353857f5cbd8947da307f\"}";
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
