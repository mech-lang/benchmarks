-- Luau adaptation; original submission and attribution retained below.
-- The Computer Language Benchmarks Game
-- https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
-- contributed by Mike Pall

local function A(i: number, j: number)
  local ij = i+j-1
  return 1.0 / (ij * (ij-1) * 0.5 + i)
end

local function Av(x: {number}, y: {number}, N: number)
  for i=1,N do
    local a = 0
    for j=1,N do a = a + x[j] * A(i, j) end
    y[i] = a
  end
end

local function Atv(x: {number}, y: {number}, N: number)
  for i=1,N do
    local a = 0
    for j=1,N do a = a + x[j] * A(j, i) end
    y[i] = a
  end
end

local function AtAv(x: {number}, y: {number}, t: {number}, N: number)
  Av(x, t, N)
  Atv(t, y, N)
end

local N = assert(tonumber(arg[1]))
local u, v, t = table.create(N, 1), table.create(N, 0), table.create(N, 0)

for i=1,10 do AtAv(u, v, t, N) AtAv(v, u, t, N) end

local vBv, vv = 0, 0
for i=1,N do
  local ui, vi = u[i], v[i]
  vBv = vBv + ui*vi
  vv = vv + vi*vi
end
io.write(string.format("%0.9f\n", math.sqrt(vBv / vv)))
