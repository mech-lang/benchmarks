use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"f6e71c397146a59f72bb1aeb30c89d3d3c10fcb360d4371826481733db962d70\",\"application.mec\":\"4d160b721421d4613e75617a001cf13c230492adc70b835ae80b31912bfc3f31\",\"factory-profile.json\":\"d36ea636c7d90acbb0e2417d689ed80ced31cfd9f78bf5b73bcf1971ec0ac45f\",\"native-descriptor.bin\":\"876b03003d16bee65a18aefaae7676d7522e7b39f6e605dd8b4c6a3d2950bf64\",\"native-descriptor.json\":\"2a8b127e647fc16d828f9ee35f9fbd5ddce08cb3c686cb0b86f8e546f7c390bc\",\"native-resources.json\":\"fb893eb29f6258ea8e293c4c61ce312746c61a9ca426567dcbdd24a864851aa8\",\"object-identity.bin\":\"2efadc9b18a3830383a3f0e269b13b91a9fdfaaf6cfcada9824db3053e13788a\",\"program.mecb\":\"050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0\",\"program.o\":\"d612ceb28aed0c80d4102f6572205873a04a5116d891a17a75dab27b8cc29dfa\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"24f2522767e00fcfd9df52be14c6af2744b3cc25e4608413c47243dc3a77e1d6\"}";
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
    assert_eq!(manifest["schema"], "mech.canonical-linked-hosted-program-application.v1");
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
