using BenchSpectralnormJulia4

empty!(ARGS)
push!(ARGS, "100")
open("/private/tmp/mech-benchmark-publication/experiments/shared/bounded-corpus-v1/cases/spectralnorm/n-100/stdin.bin", "r") do input
    mktemp() do path, output
        redirect_stdin(input) do
            redirect_stdout(output) do
                @assert BenchSpectralnormJulia4.julia_main() == 0
            end
        end
        flush(output)
        seekstart(output)
        @assert read(output) == read("/private/tmp/mech-benchmark-publication/experiments/shared/bounded-corpus-v1/cases/spectralnorm/n-100/expected.stdout")
    end
end
