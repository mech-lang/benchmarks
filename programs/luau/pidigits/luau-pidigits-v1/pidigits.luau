-- Luau adaptation of the unbounded Benchmarks Game sequential pi spigot.
-- Mr Ledrug's C program, translated by Jeremy Zerfas and Isaac Gouy; BSD-3-Clause.
-- GMP provides integer primitives; extraction, term refinement and emission are Luau.
local n = assert(tonumber(arg[1]))
local q, r, t = bigint.new(1), bigint.new(0), bigint.new(1)
local k, emitted = 1, 0
local line = ""
while emitted < n do
    local a = bigint.number(bigint.div(bigint.add(bigint.mul(q, 3), r), t))
    local b = bigint.number(bigint.div(bigint.add(bigint.mul(q, 4), r), t))
    if a == b then
        line ..= a
        emitted += 1
        r = bigint.mul(bigint.sub(r, bigint.mul(t, a)), 10)
        q = bigint.mul(q, 10)
        if emitted % 10 == 0 or emitted == n then
            io.write(line, string.rep(" ", 10 - #line), "\t:", emitted, "\n")
            line = ""
        end
    else
        local odd = 2 * k + 1
        r = bigint.mul(bigint.add(bigint.mul(q, 2), r), odd)
        q = bigint.mul(q, k)
        t = bigint.mul(t, odd)
        k += 1
    end
end
