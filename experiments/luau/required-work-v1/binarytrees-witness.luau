-- Luau adaptation; original submission and attribution retained below.
-- The Computer Language Benchmarks Game
-- https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
-- contributed by Mike Pall
-- *reset*

local function BottomUpTree(depth: number)
  if depth > 0 then
    depth = depth - 1
    local left, right = BottomUpTree(depth), BottomUpTree(depth)
    return { left, right }
  else
    return { }
  end
end

local function ItemCheck(tree)
  if tree[1] then
    return 1 + ItemCheck(tree[1]) + ItemCheck(tree[2])
  else
    return 1
  end
end


local original = BottomUpTree
local seen = {}
local allocations = 0
BottomUpTree = function(depth)
    local node = original(depth)
    assert(not seen[node], "reused tree node")
    seen[node] = true
    allocations += 1
    return node
end
local left = BottomUpTree(12)
local right = BottomUpTree(12)
assert(left ~= right)
assert(ItemCheck(left) == 8191 and ItemCheck(right) == 8191)
assert(allocations == 16382)
local a, b = BottomUpTree(0), BottomUpTree(0)
assert(a ~= b and allocations == 16384)
assert(ItemCheck(left) == 8191)
io.write("16384 distinct allocated nodes; both retained roots and distinct leaves verified\n")
