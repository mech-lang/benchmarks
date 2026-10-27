use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"3ff440a9aabe7398ce330d75995ea32e38fa51a167a544af72cff8c6e775f2f8\",\"application.mec\":\"eb36d82d0f79075a1025748352dedb67433b05729edf1d04055b100944b603e2\",\"factory-profile.json\":\"596edbe5bf88492aacbfd258d9539b8c0a4433aa54c4d1ba294927dd7542f543\",\"native-descriptor.bin\":\"45fa5291a886389c8d4425e5e5be86b56e5325c20dc01e8c3cc78301436bba98\",\"native-descriptor.json\":\"124e03e22f6624b5f352ebe9affc6eb4f5240a51a2dd66d140034c91573bd9d4\",\"object-identity.bin\":\"3091aa7e2efbc9ac3cee77cc73cda2d4775e18eaba2ee22886257a3f9d94c2cc\",\"program.mecb\":\"65f4609ed302f7a23b7ec3553fa349518f5e4b0bd9130737da7f6abbf6724d7e\",\"program.o\":\"c1dc9573fd8940f6834bc255b67b051659526209080a208ced046f56aaa97e57\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"925ca8ce01f37f8de2041057c20fcee8937f3b522926cbd3712cd3e0a68fe4e9\"}";
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
