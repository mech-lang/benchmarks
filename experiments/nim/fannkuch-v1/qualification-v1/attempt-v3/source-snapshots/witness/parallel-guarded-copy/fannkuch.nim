import std/[algorithm, os, strutils, typedthreads]

type Result = tuple[checksum: int, maximum: int]
type Job = tuple[n: int, first: int, last: int, output: ptr Result]

proc run(job: Job) {.thread.} =
  var factorial: array[13, int]
  factorial[0] = 1
  for width in 1 .. job.n:
    factorial[width] = factorial[width - 1] * width
  var permutation: array[12, int]
  var rotations: array[12, int]
  for i in 0 ..< job.n:
    permutation[i] = i
  for width in countdown(job.n, 2):
    let shift = (job.first div factorial[width - 1]) mod width
    rotations[width - 1] = shift
    for turn in 0 ..< shift:
      let first = permutation[0]
      for j in 0 ..< width - 1:
        permutation[j] = permutation[j + 1]
      permutation[width - 1] = first
  var checksum = 0
  var maximum = 0
  fannOpen(paramStr(2) / ($job.first & "-" & $job.last & ".tsv"), job.n, job.first, job.last)
  for rank in job.first ..< job.last:
    fannTraceRank = rank
    fannEvent("rank", -1, -1, permutation)
    fannEvent("rotations", -1, -1, rotations)
    var flips = 0
    if permutation[0] != 0:
      var work = permutation
      fannEvent("copy", -1, -1, work)
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
    for width in 2 .. job.n:
      let first = permutation[0]
      for j in 0 ..< width - 1:
        permutation[j] = permutation[j + 1]
      permutation[width - 1] = first
      inc rotations[width - 1]
      if rotations[width - 1] < width:
        break
      rotations[width - 1] = 0
  fannClose(job.first, job.last, checksum, maximum)
  job.output[] = (checksum, maximum)

let n = parseInt(paramStr(1))
doAssert n >= 1 and n <= 12
if paramCount() == 4:
  let first = parseInt(paramStr(3))
  let last = parseInt(paramStr(4))
  var total = 1
  for width in 1 .. n:
    total *= width
  doAssert first >= 0 and first < last and last <= total
  var result: Result
  run((n, first, last, addr result))
  echo result.checksum
  echo "Pfannkuchen(", n, ") = ", result.maximum
else:
  var total = 1
  for width in 1 .. n:
    total *= width
  let count = min(8, total)
  var mainTrace = open(paramStr(2) / "main.tsv", fmWrite)
  mainTrace.writeLine("workers\t" & $count)
  var threads: array[8, Thread[Job]]
  var results: array[8, Result]
  for worker in 0 ..< count:
    createThread(threads[worker], run, (n, total * worker div count, total * (worker + 1) div count, addr results[worker]))
    mainTrace.writeLine("created\t" & $worker & "\t" & $(total * worker div count) & "\t" & $(total * (worker + 1) div count))
  for worker in 0 ..< count:
    joinThread(threads[worker])
    mainTrace.writeLine("joined\t" & $worker)
  var checksum = 0
  var maximum = 0
  for worker in 0 ..< count:
    checksum += results[worker].checksum
    maximum = max(maximum, results[worker].maximum)
  mainTrace.close()
  echo checksum
  echo "Pfannkuchen(", n, ") = ", maximum
