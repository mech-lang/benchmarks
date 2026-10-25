use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"7f41a6f65e29fe5ebeff7cbe269b2e90d64fde2625b8daa0a8813cf5e1600287\",\"application.mec\":\"4d160b721421d4613e75617a001cf13c230492adc70b835ae80b31912bfc3f31\",\"factory-profile.json\":\"d36ea636c7d90acbb0e2417d689ed80ced31cfd9f78bf5b73bcf1971ec0ac45f\",\"native-descriptor.bin\":\"1074e4fc5a3bdec7d437e03436b84371bd84df24c9a689acb4615a3bf60b7993\",\"native-descriptor.json\":\"01a49348547e5758220b99517502c345a87db8c0795be6b4a8b8ebf0c7ac81c8\",\"native-resources.json\":\"fb893eb29f6258ea8e293c4c61ce312746c61a9ca426567dcbdd24a864851aa8\",\"object-identity.bin\":\"0ceda33e2327de37ad0ab6435f799c2b334a62820750edd74506829277598b5c\",\"program.mecb\":\"050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0\",\"program.o\":\"0bddcd82101b7665b7ece7d3d16d28e759a4f0eee53b5feffa719eb51dce1b35\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"d621ff13d0eeb7c6f9ba09ff66984a9cf98259a99335b53c5cb1c17eda344fdc\"}";
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
