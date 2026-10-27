use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"6647e3601606025496e49cfda29792bce239cbbbcd18ece45999b6878c807fdc\",\"application.mec\":\"9c887cb883696a2f3a7ae8b34e2ada6c5d958955421eca50b76fb74bf14fe226\",\"factory-profile.json\":\"351cfc108a7eb5eb5d5a149e7f497847a8959d1025798066dfc877e9290b8577\",\"native-descriptor.bin\":\"6a960064210a74ef92e693e84cdd33bb21df1c47b7b1dfe8d5b6a8ac45dca135\",\"native-descriptor.json\":\"e300b9859659d4981980f12f17382d2e2805d0e2a58b4038152201a595a5cbd5\",\"object-identity.bin\":\"8f372d0e383f5276edbb15e39a293aea7b0a27ecbac3f8c18fafaf59d8b10cdc\",\"program.mecb\":\"ff35f86a6301c3e7778a56d16170466a2a4a2c4e3d1195aedacc02164ff114f5\",\"program.o\":\"6c72b2a1f100a5143f1f7de5392ce81ce0a5e4bc4da0d9f6c2c238f2c0909ae3\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"9ecd61c0338e0fc705d4a5dc1ee94998d92fc4a903596822b07a74012e50159c\"}";
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
    assert_eq!(manifest["schema"], "mech.canonical-linked-program-application.v1");
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
