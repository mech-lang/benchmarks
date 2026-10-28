use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"074783dfad8d001d09ce79cbe2d10b620ec26e982ab1b0939e9156c5adc090a0\",\"application.mec\":\"12cadfcd00e25605f190e9d360f7f7bb661be8a02754961055ee5b6dfa84b60f\",\"factory-profile.json\":\"79d0f654577d9fe88df5c09538914bfff2a4b769de3b9042ee896bdf388ccf65\",\"native-descriptor.bin\":\"1c4022d7b9d812c0a57ec467ee7ad1d5b2ee36aa5c63c71fdd48677f3d6f0650\",\"native-descriptor.json\":\"edd9307f2777e3897b59110dfdebeb6163e3841928932438ec6cfa395b7874ee\",\"native-resources.json\":\"d38e0454052922425abad2890a855de7d8bc42266057e71be3b1b91853a56735\",\"object-identity.bin\":\"b710d233bfa514dec2092f5ee899b71f75b2e6c4e878cd47ec45ea6e0bcfa9e7\",\"program.mecb\":\"618cda5d0cc0f4a649d164fc0c3489f2bf92ed1fafead0308c23efd51baac578\",\"program.o\":\"d0acb9c45748b0896867eb03e861c40015f5c83db4f7aa14d835ee37818fe74e\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"3ff101ec0443596ea34bb01788541b333b6fa902b52cc8f5d9bd3e5a5b8fd993\"}";
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
