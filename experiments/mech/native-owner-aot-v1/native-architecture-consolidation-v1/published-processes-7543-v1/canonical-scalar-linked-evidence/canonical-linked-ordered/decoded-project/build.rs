use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"72af984692b286afca284c8ee0a1ebe6286d86460b3af8881fe14f8faae11d59\",\"application.mec\":\"3418134a79ebeca016cd62e007b288c54f7a348690605b0c23bb628214adae06\",\"factory-profile.json\":\"d97b2010c672ee0ed549ca67c5bb94a4d19fac0bdfa64bbf94ae92170d5ec99f\",\"object-identity.bin\":\"6054835be135da58388e32ad2b9cf399e3c778cfe491ff3ffbdfdbb27dd624af\",\"program.mecb\":\"58162efa045c041669c7d5519f64f4c4f5380e9ac13f20592e5d1794ddddcdfc\",\"program.o\":\"4dd3edebfd3aa0164fd7d7ecf392c0c9e7cbfa96c50c9faab3dd724fe1328bb5\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"af8aa158af2f861837293f6896fed810007170f38186ad9161f62dabb58b828b\"}";
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
    assert_eq!(manifest["schema"], "mech.canonical-linked-application.v1");
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
