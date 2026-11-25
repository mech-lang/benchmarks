use mech_core::FunctionCatalog;
use mech_engine::ProgramArtifact;
use mech_gpu::native_artifact::{
    NativeCompilationReport, NativeCompilerConfiguration,
    emit_compact_closed_object_with_configuration_for_diagnostic,
};
use std::path::Path;

pub(super) fn compile(
    artifact: &ProgramArtifact,
    catalog: &FunctionCatalog,
    out: &Path,
    include_report: bool,
) -> (Vec<u8>, serde_json::Value) {
    let config = NativeCompilerConfiguration::from_legacy_environment();
    let mut report = NativeCompilationReport::default();
    let result = emit_compact_closed_object_with_configuration_for_diagnostic(
        artifact,
        catalog,
        &config,
        false,
        include_report.then_some(&mut report),
    )
    .unwrap();
    if include_report {
        let mut json = report.json(&result.1);
        json["raw_evidence"] = serde_json::json!({
            "compiler_stages": out.join("compile.json"),
            "bytecode": out.join("program.mecb"),
            "object": out.join("program.o"),
            "native_descriptor": out.join("metadata.json"),
        });
        write(out, &json);
    }
    result
}

fn write(out: &Path, report: &serde_json::Value) {
    std::fs::write(
        out.join("host-report.json"),
        serde_json::to_vec_pretty(report).unwrap(),
    )
    .unwrap();
}

pub(super) fn finish(out: &Path, receipt: &serde_json::Value) {
    let mut report: serde_json::Value =
        serde_json::from_slice(&std::fs::read(out.join("host-report.json")).unwrap()).unwrap();
    report["source_sha256"] = receipt["source_sha256"].clone();
    report["bytecode_sha256"] = receipt["bytecode_sha256"].clone();
    report["object_sha256"] = receipt["object_sha256"].clone();
    report["driver_stages"] = receipt["phases"].clone();
    #[cfg(feature = "construction-census")]
    {
        let path = out.join("construction-census.json");
        let census: serde_json::Value =
            serde_json::from_slice(&std::fs::read(&path).unwrap()).unwrap();
        report["construction"] =
            serde_json::json!({"available": true, "counts": census, "raw": path});
    }
    write(out, &report);
}
