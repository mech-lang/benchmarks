use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"a57eaab7227c853fe3ffd0e7e9310e928ea686ccc523905737f29939e4e19ad6\",\"application.mec\":\"61261eebb484faccb4dea47090956fb43c6021907b1e5b2b19df2e31fe0e195e\",\"factory-profile.json\":\"6e19f9f3d4673ff4bb0e9d58afa48a2cfaedb888894b4786e27846c0fe9307bd\",\"object-identity.bin\":\"a66d070fcc1c56f44bbcbb8f3b6b8de59af2b99af6444ee7bcb6346054445a4b\",\"program.mecb\":\"4e518378d1b7f365b1edc89bee61b0ff916b2117d42c02c495c6d951cbe156b3\",\"program.o\":\"d4b63bf58b4a132bdecdaa53e17dd10f7cf4493c3fd5e8ad844d6e2623db6c3a\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"a491b0bb62078a0b26efa8fd2d1ebcebb2d615b2c7aec28254b1b9f5f3f16cf8\"}";
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
