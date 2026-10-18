-- Luau adaptation of Mike Pall's Benchmarks Game reverse-complement Lua #2.
-- Original ideas from Rici Lake; Lua 5.3 updates by Robin; BSD-3-Clause.
local symbols = "ACBDGHKMNSRUTWVYacbdghkmnsrutwvy"
local values = "TGVHCDMKNSYAAWBRTGVHCDMKNSYAAWBR"
local complements = {}
for i = 1, #symbols do complements[symbols:byte(i)] = values:byte(i) end
local function emit(header: string, pieces: {string})
    io.write(header, "\n")
    local sequence = table.concat(pieces)
    local output = buffer.create(65600)
    local position, column = 0, 0
    for i = #sequence, 1, -1 do
        local original = sequence:byte(i)
        local mapped = complements[original]
        if not mapped then
            error("Invalid IUPAC byte: " .. original)
        end
        buffer.writeu8(output, position, mapped)
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
local header = nil
local pieces = {}
for line in io.read():gmatch("[^\r\n]+") do
    if line:byte(1) == 62 then
        if header then emit(header, pieces) end
        header = line
        table.clear(pieces)
    elseif header and line:byte(1) ~= 59 then
        table.insert(pieces, line)
    end
end
if header then emit(header, pieces) end
