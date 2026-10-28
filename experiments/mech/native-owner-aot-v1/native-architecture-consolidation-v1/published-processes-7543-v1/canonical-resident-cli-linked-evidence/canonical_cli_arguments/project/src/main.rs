mod catalog;
mod runtime;

use std::sync::{
    Arc,
    atomic::{AtomicBool, Ordering},
};
use std::time::Duration;

use mech_core::{GenericError, MResult, MechError};

static PROGRAM: &[u8] =
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/program.mecb"
    ));

fn generated_error(message: impl Into<String>) -> MechError {
    MechError::new(GenericError { msg: message.into() }, None)
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct GeneratedArguments {
    once: bool,
    print_result: bool,
    runtime_info: bool,
    max_live_turns: Option<usize>,
    // Payload only: index zero becomes the CLI provider's one-based args/1.
    program_arguments: Vec<std::ffi::OsString>,
}

fn parse_arguments(
    arguments: impl IntoIterator<Item = std::ffi::OsString>,
) -> Result<GeneratedArguments, ()> {
    let mut parsed = GeneratedArguments {
        once: false,
        print_result: false,
        runtime_info: false,
        max_live_turns: None,
        program_arguments: Vec::new(),
    };
    let mut arguments = arguments.into_iter();
    while let Some(argument) = arguments.next() {
        if argument == std::ffi::OsStr::new("--once") {
            parsed.once = true;
        } else if argument == std::ffi::OsStr::new("--print-result") {
            parsed.print_result = true;
        } else if argument == std::ffi::OsStr::new("--runtime-info") {
            parsed.runtime_info = true;
        } else if argument == std::ffi::OsStr::new("--max-live-turns") {
            let value = arguments.next().ok_or(())?;
            let value = value.to_str().ok_or(())?.parse::<usize>().map_err(|_| ())?;
            if value == 0 {
                return Err(());
            }
            parsed.max_live_turns = Some(value);
        } else {
            if argument != std::ffi::OsStr::new("--") {
                parsed.program_arguments.push(argument);
            }
            parsed.program_arguments.extend(arguments);
            break;
        }
    }
    Ok(parsed)
}


fn usage() {
    eprintln!("usage: generated-app [--once] [--print-result] [--runtime-info] [--max-live-turns N] [--] [ARG ...]");
}

fn runtime_info_json(runtime: &mech_runtime::MechRuntime) -> String {
    let info = runtime.program_execution_info();
    let route = match info.route {
        mech_runtime::RuntimeProgramRoute::None => "none",
        mech_runtime::RuntimeProgramRoute::ResidentPure => "resident-pure",
        mech_runtime::RuntimeProgramRoute::ResidentExternal => "resident-external",
    };
    let revision = info.program_revision.map(|revision| {
        format!("\"{}\"", revision.as_bytes().iter().map(|byte| format!("{byte:02x}")).collect::<String>())
    }).unwrap_or_else(|| "null".to_string());
    let plan = info.plan_generation.map(|value| value.get().saturating_add(1).to_string()).unwrap_or_else(|| "null".to_string());
    let layout = info.layout_generation.map(|value| value.get().saturating_add(1).to_string()).unwrap_or_else(|| "null".to_string());
    format!("{{\"route\":\"{route}\",\"program_revision\":{revision},\"plan_generation\":{plan},\"layout_generation\":{layout},\"requirements\":{},\"observations\":{},\"effects\":{},\"resident_accepted_turns\":{},\"resident_rejected_turns\":{},\"coalesced_host_packets\":{},\"ignored_host_packets\":{}}}", info.requirement_count, info.observation_count, info.effect_count, info.resident_accepted_turns, info.resident_rejected_turns, info.coalesced_host_packets, info.ignored_host_packets)
}

fn run(arguments: GeneratedArguments) -> (MResult<()>, Vec<MechError>) {
    let catalog = match catalog::function_catalog() {
        Ok(catalog) => catalog,
        Err(error) => return (Err(error), Vec::new()),
    };
    let mut runtime = match runtime::runtime_builder(catalog, &arguments.program_arguments).and_then(|builder| builder.build()) {
        Ok(runtime) => runtime,
        Err(error) => return (Err(error), Vec::new()),
    };
    let runtime_constructed = true;
    let mut drivers_started = false;
    let primary = (|| -> MResult<()> {
        let durability = runtime.config().resident_durability;
        let outcome = runtime.load_bytecode_program(
            PROGRAM,
            durability,
        )?;
        let value = outcome.initial_value;

        let has_driven_inputs = runtime.has_driven_live_input_bindings()?;
        if arguments.print_result && (!arguments.once || !has_driven_inputs) && !value.is_empty() {
            println!("{}", value);
        }

        if has_driven_inputs {
            let interrupted = Arc::new(AtomicBool::new(false));
            let handler_flag = Arc::clone(&interrupted);
            ctrlc::set_handler(move || {
                handler_flag.store(true, Ordering::SeqCst);
            })
            .map_err(|error| generated_error(format!("failed to install Ctrl-C handler: {error}")))?;

            drivers_started = true;
            runtime.start_input_drivers()?;
            let mut completed_live_turns = 0usize;
            let max_live_turns = if arguments.once {
                Some(1)
            } else {
                arguments.max_live_turns
            };
            while !interrupted.load(Ordering::SeqCst) {
                if max_live_turns.is_some_and(|limit| completed_live_turns >= limit) {
                    break;
                }
                let drain_limit = max_live_turns
                    .map(|limit| limit.saturating_sub(completed_live_turns))
                    .unwrap_or(64)
                    .min(64);
                let outcomes = runtime.drain_host_inputs(drain_limit)?;
                completed_live_turns = completed_live_turns.saturating_add(
                    outcomes
                        .iter()
                        .filter(|outcome| outcome.resident_turn.is_some())
                        .count(),
                );
                if outcomes.is_empty() {
                    std::thread::sleep(Duration::from_millis(10));
                }
            }
            if arguments.once && arguments.print_result {
                if let Some((_, value)) = runtime.root_symbol_values_all()?.into_iter().next() {
                    if !value.is_empty() {
                        println!("{}", value);
                    }
                }
            }
        }
        if arguments.runtime_info {
            println!("MECH_RUNTIME_INFO {}", runtime_info_json(&runtime));
        }
        Ok(())
    })();

    let mut cleanup = Vec::new();
    if drivers_started {
        if let Err(error) = runtime.stop_input_drivers() {
            cleanup.push(error);
        }
    }
    if runtime_constructed {
        if let Err(error) = runtime.shutdown() {
            cleanup.push(error);
        }
    }
    (primary, cleanup)
}

fn main() {
    let arguments = match parse_arguments(std::env::args_os().skip(1)) {
        Ok(arguments) => arguments,
        Err(()) => {
            usage();
            std::process::exit(2);
        }
    };
    let (primary, cleanup) = run(arguments);
    let mut failed = false;
    if let Err(error) = primary {
        eprintln!("{}", error.display_message());
        failed = true;
    }
    for error in cleanup {
        eprintln!("cleanup: {}", error.display_message());
        failed = true;
    }
    if failed {
        std::process::exit(1);
    }
}
