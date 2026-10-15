using BenchRevcompJulia7

empty!(ARGS)
push!(ARGS, "0")
open("/private/tmp/mech-benchmark-publication/experiments/shared/bounded-corpus-v1/cases/revcomp/tail/stdin.bin", "r") do input
    mktemp() do path, output
        redirect_stdin(input) do
            redirect_stdout(output) do
                @assert BenchRevcompJulia7.julia_main() == 0
            end
        end
        flush(output)
        seekstart(output)
        @assert read(output) == read("/private/tmp/mech-benchmark-publication/experiments/shared/bounded-corpus-v1/cases/revcomp/tail/expected.stdout")
    end
end
