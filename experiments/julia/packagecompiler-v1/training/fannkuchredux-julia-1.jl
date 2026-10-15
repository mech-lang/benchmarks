using BenchFannkuchreduxJulia1

empty!(ARGS)
push!(ARGS, "7")
open("/private/tmp/mech-benchmark-publication/experiments/shared/bounded-corpus-v1/cases/fannkuchredux/n-7/stdin.bin", "r") do input
    mktemp() do path, output
        redirect_stdin(input) do
            redirect_stdout(output) do
                @assert BenchFannkuchreduxJulia1.julia_main() == 0
            end
        end
        flush(output)
        seekstart(output)
        @assert read(output) == read("/private/tmp/mech-benchmark-publication/experiments/shared/bounded-corpus-v1/cases/fannkuchredux/n-7/expected.stdout")
    end
end
