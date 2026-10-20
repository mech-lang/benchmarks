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
for rank in 0 ..< total:
  var flips = 0
  if permutation[0] != 0:
    var work = permutation
    while work[0] != 0:
      reverse(work, 0, work[0])
      inc flips
  checksum += (if (rank and 1) == 0: flips else: -flips)
  maximum = max(maximum, flips)
  for width in 2 .. n:
    let first = permutation[0]
    for j in 0 ..< width - 1:
      permutation[j] = permutation[j + 1]
    permutation[width - 1] = first
    inc rotations[width - 1]
    if rotations[width - 1] < width:
      break
    rotations[width - 1] = 0
echo checksum
echo "Pfannkuchen(", n, ") = ", maximum
