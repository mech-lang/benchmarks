import Common

private opaque RegexImpl : NonemptyType
def Regex : Type := RegexImpl.type

@[extern "lean_bench_regex_compile"]
opaque compileRegex (pattern : @& String) : Option Regex

@[extern "lean_bench_regex_find"]
opaque findNext (regex : @& Regex) (input : @& ByteArray) (offset : @& Nat) : Option (Nat × Nat)

def compile (pattern : String) : IO Regex :=
  match compileRegex pattern with
  | some regex => pure regex
  | none => throw (IO.userError s!"invalid regular expression: {pattern}")

def countMatches (regex : Regex) (input : ByteArray) : Nat := Id.run do
  let mut offset := 0
  let mut count := 0
  let mut finished := false
  while !finished do
    match findNext regex input offset with
    | none => finished := true
    | some (_, last) =>
      count := count + 1
      offset := last
  return count

def replaceAll (regex : Regex) (input replacement : ByteArray) : ByteArray := Id.run do
  let mut output := ByteArray.emptyWithCapacity input.size
  let mut offset := 0
  let mut finished := false
  while !finished do
    match findNext regex input offset with
    | none =>
      output := output ++ input.extract offset input.size
      finished := true
    | some (first, last) =>
      output := output ++ input.extract offset first ++ replacement
      offset := last
  return output

def main : IO Unit := do
  let input ← Bench.readAll
  let cleaned := replaceAll (← compile ">[^\n]*\n|\n") input ByteArray.empty
  for pattern in #["agggtaaa|tttaccct", "[cgt]gggtaaa|tttaccc[acg]", "a[act]ggtaaa|tttacc[agt]t",
      "ag[act]gtaaa|tttac[agt]ct", "agg[act]taaa|ttta[agt]cct", "aggg[acg]aaa|ttt[cgt]ccct",
      "agggt[cgt]aa|tt[acg]accct", "agggta[cgt]a|t[acg]taccct", "agggtaa[cgt]|[acg]ttaccct"] do
    IO.println s!"{pattern} {countMatches (← compile pattern) cleaned}"
  let mut result := cleaned
  for (pattern, replacement) in #[("tHa[Nt]", "<4>"), ("aND|caN|Ha[DS]|WaS", "<3>"),
      ("a[NSt]|BY", "<2>"), ("<[^>]*>", "|"), ("\\|[^|][^|]*\\|", "-")] do
    result := replaceAll (← compile pattern) result replacement.toUTF8
  IO.println s!"\n{input.size}\n{cleaned.size}\n{result.size}"
  Bench.finish
