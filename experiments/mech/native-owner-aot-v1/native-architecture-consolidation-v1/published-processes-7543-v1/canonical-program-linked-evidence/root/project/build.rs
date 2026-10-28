use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"2155bcce0d7db2a8080d15e133c7ba6aec6cd17d72232e9980df1f0eb387e0b3\",\"application.mec\":\"9c0232a171ce89f9d08d7edff7c127a2d7528ef9ec6226be3e583a108ab6704d\",\"factory-profile.json\":\"8f10873e714c3f6c7411a27cf372d10f5b44e1d88b7b2cbbce1ca4406601b61a\",\"native-descriptor.bin\":\"c0c8fec45b647cd1d211799156b78324d95eede8f6e99acba292c82ea87e2b08\",\"native-descriptor.json\":\"b6d6ee43cc39f077bc98bdf84abac1684de6f0f72415c1453fe31f5b335e582d\",\"object-identity.bin\":\"f8df9f70d287452294f7d7099e9c119fe9414e930629923b67cd2fc8131930a4\",\"program.mecb\":\"99305840d2c76968761284586d48c4aae599ce94088734d79b9492591a726724\",\"program.o\":\"712d770a128478a872939f9a1d09a735dd943029bd8cfd5ccd6435c88689af21\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"cb055a74c46e1ef89c4c6959671aac7e1e6c73fb1e49ce118a13c5df4952afce\"}";
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
