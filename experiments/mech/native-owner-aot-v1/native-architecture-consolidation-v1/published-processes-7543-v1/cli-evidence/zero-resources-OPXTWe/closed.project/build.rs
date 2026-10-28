use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::PathBuf};

const EXPECTED: &str = "{\"Cargo.toml\":\"49b404c37a610dffa9019a5562b4ac78209e68bfa52dfc61142ba1b3efb37e2d\",\"application.mec\":\"ed6048e3e417362d191fb2e960517d79b8ee9d20e286fff96972a024a2823283\",\"factory-profile.json\":\"a2ff1ef171376a65ee7377a98046b68335b5258185eef65b44455a5fe8547074\",\"native-descriptor.bin\":\"dad98802e4fd5ce765d11cb853bcc4a87cca01af81a4106ba1fdfcaf00f472e4\",\"native-descriptor.json\":\"6e6eda5a41dde89bd61350d4f7a3f92eac7c8cbb1890095967070d25bcfc2367\",\"native-resources.json\":\"ebafe0539a78cfd4bfc8f519d0652461b252b25dd6d3aa822eaa8daf160b16e5\",\"object-identity.bin\":\"f4b193a95f5195e395185ce55355a7033a819c532a9a329ac60ffe261629df06\",\"program.mecb\":\"09d3a35cfca493d4971a8084a23d13c7ac5aa0097107f8f3badba737fa81b421\",\"program.o\":\"210fc7217a9bbcd90f6c0a1174220a7ac75ec8974ebd9f7c6db0943e68d763fc\",\"rust-toolchain.toml\":\"19219593d7dba33a75623287af94da940a93fac92eeef99e8fff9b7fd804fcf9\",\"src/main.rs\":\"773e9b26114154a60b9b8e2da00d2024b4ffd859a475f0d650794e525e2e1730\"}";
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
