# Native, parse-only source evidence. Never include/eval/lower/macroexpand inputs.
using SHA
const J = Base.JuliaSyntax

function json(io, x)
    if x isa AbstractDict
        print(io, '{')
        for (i, key) in enumerate(sort!(collect(keys(x))))
            i > 1 && print(io, ',')
            json(io, string(key)); print(io, ':'); json(io, x[key])
        end
        print(io, '}')
    elseif x isa AbstractVector
        print(io, '[')
        for (i, value) in enumerate(x)
            i > 1 && print(io, ',')
            json(io, value)
        end
        print(io, ']')
    elseif x isa AbstractString
        print(io, '"')
        for c in x
            c == '"' ? print(io, "\\\"") : c == '\\' ? print(io, "\\\\") :
            c == '\n' ? print(io, "\\n") : c == '\r' ? print(io, "\\r") :
            c == '\t' ? print(io, "\\t") : Int(c) < 0x20 ? print(io, "\\u", string(Int(c), base=16, pad=4)) : print(io, c)
        end
        print(io, '"')
    elseif x === nothing
        print(io, "null")
    else
        print(io, x)
    end
end

function inspect(path)
    text = read(path, String)
    result = Dict{String,Any}("input" => basename(path), "source_sha256" => bytes2hex(sha256(text)))
    try
        # parseall requires complete input consumption and rejects diagnostics.
        tree = J.parseall(J.SyntaxNode, text; filename=basename(path), keep_parens=true)
        nodes = Dict{String,Any}[]
        function visit(node, parent)
            id = length(nodes) + 1
            lo, hi = J.first_byte(node), J.last_byte(node)
            item = Dict{String,Any}("id"=>id, "parent"=>parent, "kind"=>string(J.kind(node)),
                "flags"=>Int(J.flags(node)), "short_function"=>J.has_flags(node,J.SHORT_FORM_FUNCTION_FLAG),
                "start"=>lo-1, "end"=>hi, "children"=>Int[],
                "line"=>count(==(0x0a), view(codeunits(text),1:max(0,lo-1)))+1)
            push!(nodes,item)
            if J.numchildren(node) > 0
                for child in J.children(node)
                    push!(item["children"],visit(child,id))
                end
            end
            id
        end
        visit(tree,nothing)
        tokens = [Dict("kind"=>string(J.kind(t)),"start"=>Int(first(t.range))-1,
                       "end"=>Int(last(t.range)),"trivia"=>J.is_trivia(t)) for t in J.tokenize(text)]
        result["accepted"]=true; result["nodes"]=nodes; result["tokens"]=tokens
    catch error
        result["accepted"]=false; result["error"]=sprint(showerror,error)
    end
    result
end

json(stdout, Dict("schema"=>"julia-native-source-tree.v1", "version"=>string(VERSION),
    "parser"=>"Base.JuliaSyntax.parseall(SyntaxNode; keep_parens=true)",
    "input_evaluation"=>false,"macro_expansion"=>false,"lowering"=>false,
    "sources"=>[inspect(path) for path in ARGS]))
println()
