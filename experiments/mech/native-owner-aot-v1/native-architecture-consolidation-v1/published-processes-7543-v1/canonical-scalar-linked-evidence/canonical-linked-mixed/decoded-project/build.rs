use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"7fbac24e6386e4549c4081f2398e0b2307afe78f6464207b4d63090454f20bdb\",\"application.mec\":\"d7504f814201dec2f97ac1a57cb16e06cc3ce2c068e156f4646a4e18764c3042\",\"factory-profile.json\":\"207645e386325602fc112d934cf6854036930b6becde55946b39e2934d1077ed\",\"object-identity.bin\":\"583fcbc545a0e5adfd7f712185c89265d164b6fe5151111aff8398c993bf412f\",\"program.mecb\":\"0eccf9ca8dfe2cec19f918a934430524350556fad31c25ac61a5b3c515ccd7fe\",\"program.o\":\"e6d7d1a14c3dfb301bb841bbcf40c40e9c5ead40f995464bab354e51e18f120f\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"6e81c0f80c395562dcfb3f11be923585a874b56877595d442628ad7a5c040c1d\"}";
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
