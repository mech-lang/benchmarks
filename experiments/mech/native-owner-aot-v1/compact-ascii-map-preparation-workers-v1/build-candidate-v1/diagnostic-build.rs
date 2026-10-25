use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"93016060db05755bb65065e96b5bbd34698c03b9162038a49c0768331fa0a6f7\",\"application.mec\":\"4d160b721421d4613e75617a001cf13c230492adc70b835ae80b31912bfc3f31\",\"factory-profile.json\":\"d36ea636c7d90acbb0e2417d689ed80ced31cfd9f78bf5b73bcf1971ec0ac45f\",\"native-descriptor.bin\":\"f493ed8b36bc697d53f914ec145f4b2c0fb615d511b9da9e9e28fd63b03eea2a\",\"native-descriptor.json\":\"6d4335e594d9c9c5878563d503915e82b5822fe46d1ef5be5446d4167109bba4\",\"native-resources.json\":\"fb893eb29f6258ea8e293c4c61ce312746c61a9ca426567dcbdd24a864851aa8\",\"object-identity.bin\":\"80954f3fa8e6e4ebd65995766b8824a6265b4ce6ba9e8cabaeb655c87d7dd288\",\"program.mecb\":\"050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0\",\"program.o\":\"90ea49092ba3f53cd57ac80305b3bdb63d2d6db2cf32519c3c80e56b9dda7c37\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"0a46925411da6b85771991a3076d7b429235d656d545fe60b9b07e709c195224\"}";
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
