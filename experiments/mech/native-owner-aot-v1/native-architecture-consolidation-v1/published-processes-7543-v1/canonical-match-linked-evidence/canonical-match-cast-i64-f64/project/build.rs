use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"80f514b32aad85b0264b789f4fb596b5b2303b6391c34bc31976fe4de195a19e\",\"application.mec\":\"ccb3bfd78b7fef1706cb26a4f394383226742485010804628f98222c9fa9e35e\",\"factory-profile.json\":\"148adf474c9d050b1f48dd058a6d9b9ebcee786411c7b4e1e8748fdf833456b4\",\"object-identity.bin\":\"aa3940e7e3d7a75d0b5432b52801b7bc91ebfd56cc1d61f8a5176396eac4af08\",\"program.mecb\":\"4aaeb69d0023621a6ec05146c6ddad21a767ee4ecebc4129f68609ff5145c814\",\"program.o\":\"df4fa0ab952a3224fb18a0c0e4d2da73f46d8a1a7c9be295aebaabc2023283c5\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"eca1a5c6141f4108f28bf24ea7267882ad8c29f65769177cdaa896d9beb4ea45\"}";
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
