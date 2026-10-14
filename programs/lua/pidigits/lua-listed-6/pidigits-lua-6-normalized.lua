-- The Computer Language Benchmarks Game
-- https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
-- contributed by Mike Pall
-- requires LGMP which requires lua >= 5.1, < 5.4
-- with matrix optimization, courtesy of Wim Couwenberg

local g = {}
local aux = {}
require"c-gmp"(g, aux)
local add = g.mpz_add
local mul = g.mpz_mul_si
local div = g.mpz_tdiv_q
local init = g.mpz_init_set_d
local get = g.mpz_get_d

local u
local v
local w

local function produce(n1, n2, d, k)
  mul(n1, 2*k-1, u)
  add(n2, n2, v)
  mul(n1, k-1, w)
  add(u, v, n1)
  mul(n2, k+2, u)
  add(w, u, n2)
  mul(d, 2*k+1, d)
end

local function extract(n1, n2, d, y)
  mul(d, -10*y, u)
  mul(n1, 10, n1)
  add(n1, u, n1)
  mul(n2, 10, n2)
  add(n2, u, n2)
end

local function digit(n1, n2, d)
  local y = get(div(n1, d, u))
  if y == get(div(n2, d, v)) then
    return y
  end
end

-- Generate successive digits of PI.
local function pidigits(N)
  local write = io.write
  local k = 1
  local n1 = init(4)
  local n2 = init(3)
  local d = init(1)
  u = init(0)
  v = init(0)
  w = init(0)
  local i = 0
  while i < N do
    local y = digit(n1, n2, d)
    if y then
      write(y)
      i = i + 1
      if i % 10 == 0 then
        write("\t:", i, "\n")
      end
      extract(n1, n2, d, y)
    else
      produce(n1, n2, d, k)
      k = k + 1
    end
  end
  if i % 10 ~= 0 then
    write(string.rep(" ", 10 - N % 10), "\t:", N, "\n")
  end
end

local N = tonumber(arg and arg[1]) or 27
pidigits(N)
