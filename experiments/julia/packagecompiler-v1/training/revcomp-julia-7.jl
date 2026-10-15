using BenchRevcompJulia7

empty!(ARGS)
push!(ARGS, "0")
open("/private/tmp/mech-benchmark-publication/experiments/shared/bounded-corpus-v1/cases/revcomp/extended-all-iupac/stdin.bin", "r") do input
    mktemp() do path, output
        redirect_stdin(input) do
            redirect_stdout(output) do
                @assert BenchRevcompJulia7.julia_main() == 0
            end
        end
        flush(output)
        seekstart(output)
        @assert read(output) == read("/private/tmp/mech-benchmark-publication/experiments/shared/bounded-corpus-v1/cases/revcomp/extended-all-iupac/expected.stdout")
    end
end
