"""Trace-only exact source deltas; no alternative permutation or flip kernel."""
import difflib


# This helper is injected into a private COPY of the pinned algorithm module.
# The measured runtime and all original sources remain unchanged.
TRACE_HELPERS = '''var fannTraceFile* {.threadvar.}: File
var fannTraceN* {.threadvar.}: int
var fannTraceRank* {.threadvar.}: int

proc fannOpen*(path: string, n, first, last: int) =
  fannTraceFile = open(path, fmWrite)
  fannTraceN = n
  fannTraceRank = -1
  fannTraceFile.writeLine("begin\\t" & $first & "\\t" & $last & "\\t" & $n)

proc fannEvent*[T](kind: string, x, y: int, values: openArray[T]) =
  fannTraceFile.write(kind & "\\t" & $fannTraceRank & "\\t" & $x & "\\t" & $y & "\\t")
  for i in 0 ..< fannTraceN:
    if i != 0:
      fannTraceFile.write(",")
    fannTraceFile.write($values[i])
  fannTraceFile.writeLine("")

proc fannClose*(first, last, checksum, maximum: int) =
  fannTraceFile.writeLine("end\\t" & $first & "\\t" & $last & "\\t" & $checksum & "\\t" & $maximum)
  fannTraceFile.close()
  fannTraceFile = nil

'''


def replace_once(source, before, after):
    if source.count(before) != 1:
        raise ValueError('Exact instrumentation anchor changed: ' + repr(before))
    return source.replace(before, after, 1)


def library_twin(source):
    """Only an independent trace store is added after the real generic swap."""
    header = 'proc reverse*[T](a: var openArray[T], first, last: Natural) =\n'
    source = replace_once(source, header, TRACE_HELPERS + header)
    before = '  while x < y:\n    swap(a[x], a[y])\n    dec(y)\n    inc(x)\n'
    after = '  while x < y:\n    swap(a[x], a[y])\n    fannEvent("swap", x, y, a)\n    dec(y)\n    inc(x)\n'
    return replace_once(source, before, after)


def source_twin(source, parallel):
    """Add trace writes around the existing application operations only."""
    if not source.startswith('import std/['):
        raise ValueError('Unexpected source import shape')
    if not source.startswith('import std/[algorithm, '):
        source = replace_once(source, 'import std/[', 'import std/[algorithm, ')
    prefix = '  ' if parallel else ''
    indent = prefix + '  '
    loop = prefix + ('for rank in job.first ..< job.last:\n' if parallel else 'for rank in 0 ..< total:\n')
    opening = (prefix + 'fannOpen(paramStr(2) / ($job.first & "-" & $job.last & ".tsv"), job.n, job.first, job.last)\n'
        if parallel else 'fannOpen(paramStr(2) / ("0-" & $total & ".tsv"), n, 0, total)\n')
    source = replace_once(source, loop, opening + loop + indent + 'fannTraceRank = rank\n'
        + indent + 'fannEvent("rank", -1, -1, permutation)\n'
        + indent + 'fannEvent("rotations", -1, -1, rotations)\n')
    copy = 'var work = permutation\n'
    lines = source.splitlines(True)
    copies = [i for i, line in enumerate(lines) if line.strip() == copy.strip()]
    if len(copies) != 1:
        raise ValueError('Expected the exact single scratch-copy statement')
    at = copies[0]
    copy_indent = lines[at][:-len(lines[at].lstrip())]
    lines.insert(at + 1, copy_indent + 'fannEvent("copy", -1, -1, work)\n')
    source = ''.join(lines)
    while_indent = copy_indent
    source = replace_once(source, while_indent + 'while work[0] != 0:\n',
        while_indent + 'while work[0] != 0:\n' + while_indent + '  fannEvent("flip", int(work[0]), 0, work)\n')
    if 'swap(work[left], work[right])' in source:
        old = next(line for line in source.splitlines(True) if 'swap(work[left], work[right])' in line)
        swap_indent = old[:-len(old.lstrip())]
        source = replace_once(source, old, old + swap_indent + 'fannEvent("swap", left, right, work)\n')
    maximum = indent + 'maximum = max(maximum, flips)\n'
    source = replace_once(source, maximum, maximum
        + indent + 'fannEvent("done", flips, checksum, permutation)\n'
        + indent + 'fannEvent("maximum", maximum, 0, permutation)\n')
    if not parallel:
        source = replace_once(source, 'echo checksum\n',
            'fannClose(0, total, checksum, maximum)\necho checksum\n')
        return source
    source = replace_once(source, '  job.output[] = (checksum, maximum)\n',
        '  fannClose(job.first, job.last, checksum, maximum)\n  job.output[] = (checksum, maximum)\n')
    begin = 'var threads: array[8, Thread[Job]]\n'
    source = replace_once(source, begin,
        'var mainTrace = open(paramStr(2) / "main.tsv", fmWrite)\n'
        + 'mainTrace.writeLine("workers\\t" & $count)\n' + begin)
    create = '  createThread(threads[worker], run, (n, total * worker div count, total * (worker + 1) div count, addr results[worker]))\n'
    source = replace_once(source, create, create
        + '  mainTrace.writeLine("created\\t" & $worker & "\\t" & $(total * worker div count) & "\\t" & $(total * (worker + 1) div count))\n')
    join = '  joinThread(threads[worker])\n'
    source = replace_once(source, join, join + '  mainTrace.writeLine("joined\\t" & $worker)\n')
    source = replace_once(source, 'echo checksum\n', 'mainTrace.close()\necho checksum\n')
    # The optional diagnostic entry calls the SAME original worker on an exact
    # arbitrary global interval. Normal witness mode retains the original
    # scheduler. This branch is never part of a production/timed binary.
    top = source.index('let n = parseInt(paramStr(1))\n')
    body = source[top:]
    declaration, body = body.split('doAssert n >= 1 and n <= 12\n', 1)
    original = ''.join('  ' + line if line.strip() else line for line in body.splitlines(True))
    entry = declaration + 'doAssert n >= 1 and n <= 12\n'
    entry += '''if paramCount() == 4:
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
'''
    return source[:top] + entry + original


def difference(before, after, before_name, after_name):
    return ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
        fromfile=before_name, tofile=after_name))
