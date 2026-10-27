use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"aa7a37bb503563acfc891b47a68dd2d0617cd36d1fc4bd824825810813a5c243\",\"application.mec\":\"12cadfcd00e25605f190e9d360f7f7bb661be8a02754961055ee5b6dfa84b60f\",\"factory-profile.json\":\"79d0f654577d9fe88df5c09538914bfff2a4b769de3b9042ee896bdf388ccf65\",\"native-descriptor.bin\":\"98947a0220eea7eea1c5b81577c4da7c16fc11b2165847aa1d2f2cc53fb483c4\",\"native-descriptor.json\":\"1f927d52d0b00c032a135563466dd5261904f5a60a9709ef8d08b73ab530dda0\",\"native-resources.json\":\"9c29675b7101dca3c8a18cf3b539a68691f258f832e7228bed414ce5e4829f16\",\"object-identity.bin\":\"fbe4d46990d586ac542c1a8bdba3056a95136336d898c3894b6cbd04661f4853\",\"program.mecb\":\"6ca5c43d52ab437cdae52bf8cf1931e18f92fbbf0e7c8b1fbd9d6d00c09d2551\",\"program.o\":\"584359070736129fa1648b5dbec0d03419d7cccb1feaa2e795c849fb6817d806\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"8f53fef9e0b751f5f6cd04bb4c280888fab4743ad58c28fdff5af878908d8c64\"}";
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
    assert_eq!(manifest["schema"], "mech.canonical-linked-benchmark-program-application.v1");
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
