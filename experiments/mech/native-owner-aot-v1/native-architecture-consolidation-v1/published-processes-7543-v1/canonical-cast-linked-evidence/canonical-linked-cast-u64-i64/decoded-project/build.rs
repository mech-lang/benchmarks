use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"bbda98bfbe699e9c53f340aba9f132cd7d82fcba62801603c6718f296effd875\",\"application.mec\":\"6eeeee7c406b801cc57e10d1a2f600fda7b11960eef834a3878396f5b0c9e41f\",\"factory-profile.json\":\"2bef780f39514a41f512fecb28ec270f3bd4f12d7a17a6613ca0aa805f69b005\",\"object-identity.bin\":\"cd58a80d908ff034deb92310b7f35cf0a3ef8102931afba2f39b538935f615c2\",\"program.mecb\":\"78a7d0ff42fa6a62c51cfc6dd01ea196b568ee87646301f582d1a23d9b73e3c5\",\"program.o\":\"b3ce8dc3468506aa18e6013f814caf431ab9d32e93c49ac44c557b88fe58b296\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"1e20b03e8b4f743db2facf32b8da135e1a83205568105267a597bbecb84a9286\"}";
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
