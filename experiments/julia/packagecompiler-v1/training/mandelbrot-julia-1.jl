using BenchMandelbrotJulia1

empty!(ARGS)
push!(ARGS, "64")
open("/private/tmp/mech-benchmark-publication/experiments/shared/bounded-corpus-v1/cases/mandelbrot/n-64/stdin.bin", "r") do input
    mktemp() do path, output
        redirect_stdin(input) do
            redirect_stdout(output) do
                @assert BenchMandelbrotJulia1.julia_main() == 0
            end
        end
        flush(output)
        seekstart(output)
        @assert read(output) == read("/private/tmp/mech-benchmark-publication/experiments/shared/bounded-corpus-v1/cases/mandelbrot/n-64/expected.stdout")
    end
end
