use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"b5e8f689158668346d847ab35bf9525efd6f728376e8d3399769312f0ad2780f\",\"application.mec\":\"a46b7c88d5c425a8e9a11e31d4fb68abab7a1de54dc757faf4690f0967de40c8\",\"factory-profile.json\":\"d6310abf5ae0f33b4ba0832cb228e8d082d91e843a755d2a7c6935dff5b791e6\",\"native-descriptor.bin\":\"d2ba331ab6ddd7c115293070968213665555308aa483b6c0593a70d7ae001e19\",\"native-descriptor.json\":\"fcaca8cf2bd7d265b1caa479cdd8461590369ef6e58c7aefea1dd3098328d7e8\",\"native-resources.json\":\"affa5a7f983277a1e7f61502444c56e29d26ca41b0f9e8a29585d1dec8b00826\",\"object-identity.bin\":\"e6a2f201c1668a17a15817b7f56bb08006d2f321c866aa2491d3fcb034e32efa\",\"program.mecb\":\"77a2210ff3c8fb59358b75fe955a0f31761f5b96c938a7f70b66988c8e1b26a5\",\"program.o\":\"71d2776df9dc81890967391884ea22b140c0895f26054ca0b1f599dc11989864\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"c352c93f763c57ca67aff0ad6b0f306aee8222c77e0123553ed78b6c5cabc286\"}";
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
