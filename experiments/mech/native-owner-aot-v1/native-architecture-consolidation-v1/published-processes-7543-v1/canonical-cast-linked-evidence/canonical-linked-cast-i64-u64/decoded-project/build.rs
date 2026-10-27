use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"69c8de694422e12bd1a3de29e4d4c53baf6e465e571a7e762979e76fc9aca0ce\",\"application.mec\":\"21a02e832b4779d8c4ac6dad6b99550186a90f94ef5f76731b5fae040528a8e2\",\"factory-profile.json\":\"2bef780f39514a41f512fecb28ec270f3bd4f12d7a17a6613ca0aa805f69b005\",\"object-identity.bin\":\"2016ebca44c18c7421f4760db5be38837cfc3a3e064c00ddf4dbe0c7796de96a\",\"program.mecb\":\"45f9de58a0c9b9d4e63262f2b6a9dbc07965c81e68a93ccc2b6f74b5e88ab367\",\"program.o\":\"0a13b2bcd8225bc220f8cbb7f5e944cfb098891e0a9aa02a432c60e231e2b4c1\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"388dc6e3cda8f6acbb817d869650cba161737027501e7484fff42f7ace70445c\"}";
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
