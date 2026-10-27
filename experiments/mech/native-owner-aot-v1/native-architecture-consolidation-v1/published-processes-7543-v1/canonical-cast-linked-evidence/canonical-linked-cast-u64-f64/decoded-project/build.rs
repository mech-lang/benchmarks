use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"f1be32828b1eb783de7097d2cfaa545848f0176708e04611dce3b14090ea74c5\",\"application.mec\":\"966c99abcfddc7bc8a0dd8b0efa7644030beb3c0ba3136b64a4495fdb1e9b1a6\",\"factory-profile.json\":\"6e19f9f3d4673ff4bb0e9d58afa48a2cfaedb888894b4786e27846c0fe9307bd\",\"object-identity.bin\":\"0e5de572e9b18f84b4bdd3451ca18eb2786c80a3da05bcb74ccab39190f7e689\",\"program.mecb\":\"1933f71dffb7a5c624a0ae58561110e0eaa8bd5b03bf9d522f412e49f40715a5\",\"program.o\":\"baec9938a2dc7281e760f3ac8d133e3235e23cc9c05fc2da39ea10fd19007150\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"861a51d2b42487afafb45fabded96eb2d88f21e65a29e41b10a7554418c04c06\"}";
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
