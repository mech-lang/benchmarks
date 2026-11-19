//! Public source-native sequence lane. Kept separate from canonical resident results.
fn main() {
    if let Err(error)=mech_gpu::execution::run_cli() {
        eprintln!("{error}");std::process::exit(1);
    }
}
