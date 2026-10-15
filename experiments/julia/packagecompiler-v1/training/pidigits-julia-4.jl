using BenchPidigitsJulia4

empty!(ARGS)
push!(ARGS, "97")
open("/private/tmp/mech-benchmark-publication/experiments/shared/bounded-corpus-v1/cases/pidigits/n-97/stdin.bin", "r") do input
    mktemp() do path, output
        redirect_stdin(input) do
            redirect_stdout(output) do
                @assert BenchPidigitsJulia4.julia_main() == 0
            end
        end
        flush(output)
        seekstart(output)
        @assert read(output) == read("/private/tmp/mech-benchmark-publication/experiments/shared/bounded-corpus-v1/cases/pidigits/n-97/expected.stdout")
    end
end
