use std::{collections::BTreeMap, sync::Arc};

use mech_core::{FunctionCatalog, MResult};
use mech_runtime::{
    ConfigValue, DiagnosticsConfig, HostInstanceConfig, LogLevel,
    ResidentDurabilityPolicy, RunResourceGrantConfig, RuntimeBuilder, RuntimeConfig, RuntimeLimits,
};

pub fn runtime_builder(
    catalog: Arc<FunctionCatalog>,
    program_arguments: &[std::ffi::OsString],
) -> MResult<RuntimeBuilder> {
    let config = RuntimeConfig {
        name: "canonical-cli-qualification".to_string(),
        resident_durability: ResidentDurabilityPolicy::Volatile,
        limits: RuntimeLimits {
            max_steps_per_turn: Some(10000u64),
            max_turn_duration_ms: Some(1000u64),
            max_memory_bytes: None,
            max_tasks: Some(10000u64),
            max_actors: Some(10000u64),
            max_actor_mailbox_len: Some(10000u64),
            max_source_bytes: Some(10485760u64),
            max_in_memory_events: Some(100000u64),
        },
        diagnostics: DiagnosticsConfig {
            trace_enabled: false,
            profile_enabled: false,
            debug_enabled: false,
            log_level: LogLevel::Info,
        },
    };

    let mut builder = RuntimeBuilder::new()
        .function_catalog(catalog)
        .config(config);

    builder = builder.host_factory(
        Box::new(
            mech_terminal::CliHostFactory::with_arguments(program_arguments.to_vec())?,
        ),
    )?;

    builder = builder.host_instance(HostInstanceConfig {
        name: "cli".to_string(),
        provider: "cli".to_string(),
        settings: ConfigValue::Map(BTreeMap::new()),
    });

    builder = builder.run_resource_grant(RunResourceGrantConfig {
        target: "cli/args".to_string(),
        operations: vec!["read".to_string()],
        paths: vec!["1".to_string()],
    });

    builder = builder.run_resource_grant(RunResourceGrantConfig {
        target: "cli/args".to_string(),
        operations: vec!["read".to_string()],
        paths: vec!["2".to_string()],
    });

    builder = builder.run_resource_grant(RunResourceGrantConfig {
        target: "cli/stdout".to_string(),
        operations: vec!["write".to_string()],
        paths: vec!["text".to_string()],
    });

    Ok(builder)
}
