using BenchKnucleotideJulia1

empty!(ARGS)
push!(ARGS, "0")
open("/private/tmp/mech-benchmark-publication/experiments/julia/packagecompiler-v1/training-fixtures/knucleotide/clbg-shape/stdin.bin", "r") do input
    mktemp() do path, output
        redirect_stdin(input) do
            redirect_stdout(output) do
                @assert BenchKnucleotideJulia1.julia_main() == 0
            end
        end
        flush(output)
        seekstart(output)
        @assert read(output) == read("/private/tmp/mech-benchmark-publication/experiments/julia/packagecompiler-v1/training-fixtures/knucleotide/clbg-shape/expected.stdout")
    end
end
