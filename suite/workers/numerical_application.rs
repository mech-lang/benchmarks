//! Public canonical-artifact numeric runner, including its complete CLI lifecycle.
fn main() {
    if let Err(error)=mech_gpu::fused_f64::runner::run_cli() {
        eprintln!("{error}");std::process::exit(1);
    }
}
