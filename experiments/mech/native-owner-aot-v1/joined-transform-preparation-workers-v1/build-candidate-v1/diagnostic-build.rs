use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"6972f5c96e41ea01801c323f12bebc04f4f1cead15d514499d535b5599400fe4\",\"application.mec\":\"4d160b721421d4613e75617a001cf13c230492adc70b835ae80b31912bfc3f31\",\"factory-profile.json\":\"d36ea636c7d90acbb0e2417d689ed80ced31cfd9f78bf5b73bcf1971ec0ac45f\",\"native-descriptor.bin\":\"acccef09eb1c036d59442d1c18ede741dd50dc39e1af4483b9205b1822d57cce\",\"native-descriptor.json\":\"4ed9ec7534157630f24b94e7cc26e369e525c18c96515057f406f25356efa693\",\"native-resources.json\":\"fb893eb29f6258ea8e293c4c61ce312746c61a9ca426567dcbdd24a864851aa8\",\"object-identity.bin\":\"4d5688fc365e5f7bb78c1cb117a18f1a00df14e341fa8e5ba1319de0bc2eb1a9\",\"program.mecb\":\"050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0\",\"program.o\":\"5d898ffbb2487628c6ff8b461345ec94a3dff4478a1b481bc43a99d77089375c\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"2bdb18878fa9eea0738ae6c377d5137f605f0454ccf2a6ed5715c3cbcdd612e0\"}";
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
