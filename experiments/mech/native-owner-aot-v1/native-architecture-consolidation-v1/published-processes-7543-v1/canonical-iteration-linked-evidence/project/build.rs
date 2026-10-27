use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"f8a85d37e6335e6a5e1ad793b39db4d6c2f90ca46222a508ed684699cb54d1b8\",\"application.mec\":\"879a05c0c1bf51217599ac6409386930a350c3874a64c1d730a72784f2648970\",\"factory-profile.json\":\"93db1411d55c2aceb5edd787a1220faf66dc4dfbafac85ea6f415c771193e979\",\"object-identity.bin\":\"3ec1027649223234a26394339675f2888a678fe5ba0cbd3481b5def80c0268d7\",\"program.mecb\":\"bde9ffb5d62d1c486f48dbab786fbff23caa8d8b4eec093b2442d62d4f9c22b9\",\"program.o\":\"ee401afc42e1a8f8d3ca8d19111a31b86d48dde0cefb1e7ec3bed31f1116572c\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"617573a738d4131b7e3c094f24ff5aaf3cc8c4f556a2bff772d85a1d83ba3c33\"}";
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
    assert_eq!(manifest["schema"], "mech.canonical-linked-iteration-application.v1");
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
