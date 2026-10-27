use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"fe0715b66f93901b50bcae4edd0a413acc74526450ee0b7af6a7b3247a4e0e1c\",\"application.mec\":\"34f170403c63f46aea636adaabe4534cbc608e90a702e6110b0d8dab13f22542\",\"factory-profile.json\":\"79d0f654577d9fe88df5c09538914bfff2a4b769de3b9042ee896bdf388ccf65\",\"native-descriptor.bin\":\"e68255f48caa3f6527c16766e4c03c7e7d7412acb76539ff9e78acf05f752f2b\",\"native-descriptor.json\":\"7661f60565511ca3f593e2ec6a570cb4b78af3cac925726d3364db7abf10734a\",\"native-resources.json\":\"039f8d8f3e262cb043ba153d0b5066c27cf7c7c465d662c181fdae336b7b5c25\",\"object-identity.bin\":\"ed62fd39234c126cbfb06bb6385d820ee00d62fa9cbc9309b06d19d026768fd6\",\"program.mecb\":\"b7e8b5245fa32778848d06b346b54f532e41c1d8ff0f9cb41b88a66c4a57831c\",\"program.o\":\"5a7e4256522b046fa24d9450a9ba2450dbbe849f02de662412583893356ae447\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"7a33db61834b2680ad8731ce2adcef2a18bd93ccdf045ef0ba305f879849ccb9\"}";
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
