import std/[algorithm, os, strutils]

let n = parseInt(paramStr(1))
doAssert n >= 1 and n <= 12
var permutation: array[12, int]
var rotations: array[12, int]
var total = 1
for i in 0 ..< n:
  permutation[i] = i
  total *= i + 1
var checksum = 0
var maximum = 0
fannOpen(paramStr(2) / ("0-" & $total & ".tsv"), n, 0, total)
for rank in 0 ..< total:
  fannTraceRank = rank
  fannEvent("rank", -1, -1, permutation)
  fannEvent("rotations", -1, -1, rotations)
  var work = permutation
  fannEvent("copy", -1, -1, work)
  var flips = 0
  while work[0] != 0:
    fannEvent("flip", int(work[0]), 0, work)
    var left = 0
    var right = work[0]
    while left < right:
      swap(work[left], work[right])
      fannEvent("swap", left, right, work)
      inc left
      dec right
    inc flips
  checksum += (if (rank and 1) == 0: flips else: -flips)
  maximum = max(maximum, flips)
  fannEvent("done", flips, checksum, permutation)
  fannEvent("maximum", maximum, 0, permutation)
  for width in 2 .. n:
    let first = permutation[0]
    for j in 0 ..< width - 1:
      permutation[j] = permutation[j + 1]
    permutation[width - 1] = first
    inc rotations[width - 1]
    if rotations[width - 1] < width:
      break
    rotations[width - 1] = 0
fannClose(0, total, checksum, maximum)
echo checksum
echo "Pfannkuchen(", n, ") = ", maximum
