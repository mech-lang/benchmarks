use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"66e98f13318c50f85c14d431f20c22be5903a8496c61db2a8465c78eeea8a26b\",\"application.mec\":\"4d160b721421d4613e75617a001cf13c230492adc70b835ae80b31912bfc3f31\",\"factory-profile.json\":\"d36ea636c7d90acbb0e2417d689ed80ced31cfd9f78bf5b73bcf1971ec0ac45f\",\"native-descriptor.bin\":\"be94b1aff90a50030ca6a023e61175d913c3bd24f15c5b89d4467558761f8049\",\"native-descriptor.json\":\"c2c6e927cf5055bcba7d78f0ed0b1fb3c0965751fc5e75197ba7b533baa1a296\",\"native-resources.json\":\"fb893eb29f6258ea8e293c4c61ce312746c61a9ca426567dcbdd24a864851aa8\",\"object-identity.bin\":\"a79b421c04ed4f4432700ae2584a46a64212e9bbff032c2be120942c59c956f4\",\"program.mecb\":\"050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0\",\"program.o\":\"f25ada28ff389713076fcb342b3b13f807741bfda91ca2274e6eb4d8ebc36335\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"941068798a7c37e55119c0c576f81b89b06af91dd0697c2ffd148ca468ca92b0\"}";
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
