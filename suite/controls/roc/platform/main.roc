platform "matched-compression"
    requires { run : List(U8), List(U8) -> List(U8) }
    exposes []
    packages {}
    provides { "roc_compress": run_for_host }
    hosted {}
    targets: { inputs_dir: "targets/", arm64mac: { inputs: [app], output: Archive } }

run_for_host : List(U8), List(U8) -> List(U8)
run_for_host = run
