use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"9ebcc58491f8b9574cb3ab58f364e3eec14a56926fc90f3d4e9c30f7f1f60c34\",\"application.mec\":\"9a6d6c35ef5fbc897091f5181dd44c669e3f87fb32f779b0b21a6ced151da78c\",\"factory-profile.json\":\"b33a8362362d9526c306b2830f00d07d38946f2289ab75b2cd0786a99fbf4f43\",\"object-identity.bin\":\"401007879da6cf1f472cad1a9227e8fea235be20fa99fb6a4cb41335cda7ece3\",\"program.mecb\":\"6b9ad60022091d3e0ecaee44e1be46944820db22ce928012833ee0127012e236\",\"program.o\":\"25c7ac8ba71a973dc30fdb472edc29737c4e41d7b7a270e341d1afc4624d396e\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"07b4ef20ce53ac9d974667b9a0dc617ed23cd0b49b0f99c2dda4f2ff22e75096\"}";
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
