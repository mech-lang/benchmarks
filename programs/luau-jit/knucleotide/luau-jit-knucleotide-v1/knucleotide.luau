-- Luau adaptation of Mike Pall's Benchmarks Game k-nucleotide Lua #2.
-- BSD-3-Clause; rolling numeric keys replace temporary substring keys.
local selected = false
local lines = {}
for line in io.read():gmatch("[^\r\n]+") do
    if line:byte(1) == 62 then
        if selected then break end
        local nextByte = line:byte(7)
        selected = line:sub(1, 6) == ">THREE" and (nextByte == nil or nextByte == 32 or nextByte == 9)
    elseif selected and line:byte(1) ~= 59 then
        table.insert(lines, line:upper())
    end
end
local sequence = table.concat(lines)
local codes = buffer.create(#sequence)
local alphabet = { [65] = 0, [67] = 1, [71] = 2, [84] = 3 }
for i = 1, #sequence do
    local code = alphabet[sequence:byte(i)]
    assert(code ~= nil, "invalid nucleotide in THREE record")
    buffer.writeu8(codes, i - 1, code)
end
local function histogram(width: number)
    local modulus = 4 ^ width
    local counts = table.create(modulus, 0)
    local key = 0
    for i = 0, #sequence - 1 do
        key = (key * 4 + buffer.readu8(codes, i)) % modulus
        if i + 1 >= width then counts[key + 1] += 1 end
    end
    return counts
end
local function decode(key: number, width: number): string
    local text = ""
    for _ = 1, width do
        local code = key % 4
        text = ("ACGT"):sub(code + 1, code + 1) .. text
        key = math.floor(key / 4)
    end
    return text
end
local function frequencies(width: number)
    local counts = histogram(width)
    local order = {}
    for key, count in counts do
        if count > 0 then table.insert(order, key) end
    end
    table.sort(order, function(a, b)
        return counts[a] > counts[b] or (counts[a] == counts[b] and a < b)
    end)
    for _, key in order do
        io.write(string.format("%s %.3f\n", decode(key - 1, width), 100 * counts[key] / (#sequence - width + 1)))
    end
    io.write("\n")
end
frequencies(1)
frequencies(2)
for _, query in {"GGT", "GGTA", "GGTATT", "GGTATTTTAATT", "GGTATTTTAATTTATAGT"} do
    local wanted, key, count = 0, 0, 0
    for i = 1, #query do wanted = wanted * 4 + alphabet[query:byte(i)] end
    local modulus = 4 ^ #query
    for i = 0, #sequence - 1 do
        key = (key * 4 + buffer.readu8(codes, i)) % modulus
        if i + 1 >= #query and key == wanted then count += 1 end
    end
    io.write(string.format("%d\t%s\n", count, query))
end
