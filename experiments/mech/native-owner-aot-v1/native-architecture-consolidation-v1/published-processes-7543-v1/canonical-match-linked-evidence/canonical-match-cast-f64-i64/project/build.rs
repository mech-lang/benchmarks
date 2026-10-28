use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"e9ce3910c83657cf774ff271f6d699d11fc768112a5230a590bee18c69837461\",\"application.mec\":\"0cfd83f9498f826f27110726cae2590522a3e94f3d8a9f23562bf06ca978e38a\",\"factory-profile.json\":\"148adf474c9d050b1f48dd058a6d9b9ebcee786411c7b4e1e8748fdf833456b4\",\"object-identity.bin\":\"e5f43cbd7fca96a96eb768047794d1ddb03c0e57c41ceb86769d3a57df208ce5\",\"program.mecb\":\"6dfb6203e0936a733abde439a3927d3c06927fb1ac1d7fdb4df5dc310c96dbde\",\"program.o\":\"c26d52becb8d93b6580e24d501e282a5c163a72d31d09d24714ba8e98c79ca6a\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"9d7bad6ffdc81ab45eedc429c2681373f8a03dfff5c340d71eda8c321a3ba53a\"}";
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
