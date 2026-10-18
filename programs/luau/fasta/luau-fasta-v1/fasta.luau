-- Luau adaptation of the Benchmarks Game FASTA Lua #2 submission.
-- Original algorithm contributed by Mike Pall, modified by Robin; BSD-3-Clause.
local seed = 42
local function repeatSequence(header: string, sequence: string, n: number)
    io.write(header, "\n")
    local doubled = sequence .. sequence
    local position = 1
    local lines = {}
    for first = 1, n, 60 do
        local width = math.min(60, n - first + 1)
        table.insert(lines, doubled:sub(position, position + width - 1) .. "\n")
        position = (position + width - 1) % #sequence + 1
        if #lines == 1024 then
            io.write(table.concat(lines))
            table.clear(lines)
        end
    end
    io.write(table.concat(lines))
end
local function randomSequence(header: string, distribution: {{any}}, n: number)
    io.write(header, "\n")
    local lookup = table.create(139968, 0)
    local index, cumulative = 1, distribution[1][2]
    for value = 0, 139967 do
        while value / 139968 >= cumulative and index < #distribution do
            index += 1
            cumulative += distribution[index][2]
        end
        lookup[value + 1] = string.byte(distribution[index][1])
    end
    local output = buffer.create(65600)
    local position, column = 0, 0
    for _ = 1, n do
        seed = (seed * 3877 + 29573) % 139968
        buffer.writeu8(output, position, lookup[seed + 1])
        position += 1
        column += 1
        if column == 60 then
            buffer.writeu8(output, position, 10)
            position += 1
            column = 0
        end
        if position >= 65536 then
            io.write(buffer.readstring(output, 0, position))
            position = 0
        end
    end
    if column ~= 0 then
        buffer.writeu8(output, position, 10)
        position += 1
    end
    io.write(buffer.readstring(output, 0, position))
end
local alu = "GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGG"
    .. "GAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGA"
    .. "CCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAAT"
    .. "ACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCA"
    .. "GCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGG"
    .. "AGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCC"
    .. "AGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA"
local n = assert(tonumber(arg[1]))
repeatSequence(">ONE Homo sapiens alu", alu, n * 2)
randomSequence(">TWO IUB ambiguity codes", {
    {"a", .27}, {"c", .12}, {"g", .12}, {"t", .27}, {"B", .02}, {"D", .02},
    {"H", .02}, {"K", .02}, {"M", .02}, {"N", .02}, {"R", .02}, {"S", .02},
    {"V", .02}, {"W", .02}, {"Y", .02}
}, n * 3)
randomSequence(">THREE Homo sapiens frequency", {
    {"a", .3029549426680}, {"c", .1979883004921}, {"g", .1975473066391}, {"t", .3015094502008}
}, n * 5)
