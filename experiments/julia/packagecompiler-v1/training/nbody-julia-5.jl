using BenchNbodyJulia5

empty!(ARGS)
push!(ARGS, "1000")
mktemp() do path, output
    redirect_stdout(output) do
        @assert BenchNbodyJulia5.julia_main() == 0
    end
end
