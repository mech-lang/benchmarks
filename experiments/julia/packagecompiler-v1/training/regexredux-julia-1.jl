using BenchRegexreduxJulia1

empty!(ARGS)
push!(ARGS, "0")
open("/private/tmp/mech-benchmark-publication/experiments/shared/bounded-corpus-v1/cases/regexredux/specified-all-count-alternatives/stdin.bin", "r") do input
    mktemp() do path, output
        redirect_stdin(input) do
            redirect_stdout(output) do
                @assert BenchRegexreduxJulia1.julia_main() == 0
            end
        end
        flush(output)
        seekstart(output)
        @assert read(output) == read("/private/tmp/mech-benchmark-publication/experiments/shared/bounded-corpus-v1/cases/regexredux/specified-all-count-alternatives/expected.stdout")
    end
end
