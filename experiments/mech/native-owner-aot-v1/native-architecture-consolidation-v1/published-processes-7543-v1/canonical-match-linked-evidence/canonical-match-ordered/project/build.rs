use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"a62af93d96e14afab17cf670822e7edfedb10e002f7193cc0935279e7de68e34\",\"application.mec\":\"1e9c5453c95bad17f4a25d516351a1dc25e1b148afa3176760713ec76a0306dd\",\"factory-profile.json\":\"a334e2c5d3c9a5b08658081e729822e0637b45f3edbdecf0c217c7e0aa6b26d0\",\"object-identity.bin\":\"d1e7571e43638f874a7cf20f6dcfde2adc9bf8d7b3274b1a688c14c62dc5b5bf\",\"program.mecb\":\"170e1f543bcc83f8751e87adde19ff0a916dbdc1ce24934dde569fd435f339a7\",\"program.o\":\"58ad5120dc51b7e9371b1a84ac560615d98386a0f0474b3893a40a6b37bf7082\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"44bf142bec3e0f20883bfbefab3b164520464778b8c8adfe3d05ce8e56aeaae2\"}";
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
