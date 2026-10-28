use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"78dbabf3ebbc8316e6e60c1c259139a2d521c8a5ee15c118f01695592ff1e35c\",\"application.mec\":\"52f891b486972b61bc377ece2e143cf48c9ec792e379a49ae41bbd18d54b69f3\",\"factory-profile.json\":\"dde53b11f71a7e5764db8155d1fc2f95094c617c8e0be0f30b54bf450216720d\",\"object-identity.bin\":\"75bc4387111f1b1b3ad10406e2c2956c2a9d5ab74c0b6b3c2f2d61544b6fc588\",\"program.mecb\":\"6a7f484d5981bf5587adda18266fecc55578c451c72c7f8deaa3d70fde5c1027\",\"program.o\":\"966c46baffa5261a73c487068e78b714a2656710138cebc48140ef8a52ad3cd7\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"d32a9064c2ac3478999fadd34bfc8059edf1116285e1dcaa18f9f3a0f7ce1f9b\"}";
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
