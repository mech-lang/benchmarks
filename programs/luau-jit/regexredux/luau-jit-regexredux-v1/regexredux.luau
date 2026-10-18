-- Luau adaptation of Jeremy Zerfas's Benchmarks Game regex-redux Lua #1.
-- BSD-3-Clause. The general regex API is PCRE2; orchestration remains in Luau.
local input = io.read()
local sequence = regex.replace(regex.new(">.*\n|\n"), input, "")
for _, pattern in {
    "agggtaaa|tttaccct", "[cgt]gggtaaa|tttaccc[acg]", "a[act]ggtaaa|tttacc[agt]t",
    "ag[act]gtaaa|tttac[agt]ct", "agg[act]taaa|ttta[agt]cct", "aggg[acg]aaa|ttt[cgt]ccct",
    "agggt[cgt]aa|tt[acg]accct", "agggta[cgt]a|t[acg]taccct", "agggtaa[cgt]|[acg]ttaccct"
} do
    local compiled = regex.new(pattern)
    local position, count = 1, 0
    while true do
        local first, last = regex.find(compiled, sequence, position)
        if not first then break end
        count += 1
        position = last + 1
    end
    io.write(string.format("%s %d\n", pattern, count))
end
local result = sequence
for _, replacement in {
    {"tHa[Nt]", "<4>"}, {"aND|caN|Ha[DS]|WaS", "<3>"}, {"a[NSt]|BY", "<2>"},
    {"<[^>]*>", "|"}, {"\\|[^|][^|]*\\|", "-"}
} do
    result = regex.replace(regex.new(replacement[1]), result, replacement[2])
end
io.write(string.format("\n%d\n%d\n%d\n", #input, #sequence, #result))
