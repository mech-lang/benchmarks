import Common

def alu := ("GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGG" ++
  "GAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGA" ++
  "CCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAAT" ++
  "ACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCA" ++
  "GCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGG" ++
  "AGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCC" ++
  "AGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA").toUTF8

def repeated (n : Nat) : IO Unit := do
  let mut output := ByteArray.emptyWithCapacity 65536
  let mut position := 0
  for i in [:n] do
    output := output.push alu[position]!
    position := (position + 1) % alu.size
    if i % 60 == 59 || i + 1 == n then output := output.push 10
    if output.size >= 65536 then
      Bench.writeBytes output
      output := ByteArray.emptyWithCapacity 65536
  Bench.writeBytes output

def randomSequence (n : Nat) (alphabet : ByteArray) (probabilities : Array Float) (seed : UInt64) : IO UInt64 := do
  let mut cumulative := #[]
  let mut sum := 0.0
  for p in probabilities do
    sum := sum + p
    cumulative := cumulative.push sum
  let mut state := seed
  let mut output := ByteArray.emptyWithCapacity 65536
  for i in [:n] do
    state := (state * 3877 + 29573) % 139968
    let random := state.toFloat / 139968.0
    let mut index := 0
    while index + 1 < alphabet.size && random >= cumulative[index]! do index := index + 1
    output := output.push alphabet[index]!
    if i % 60 == 59 || i + 1 == n then output := output.push 10
    if output.size >= 65536 then
      Bench.writeBytes output
      output := ByteArray.emptyWithCapacity 65536
  Bench.writeBytes output
  return state

def main (args : List String) : IO Unit := do
  let n ← Bench.argument args
  IO.println ">ONE Homo sapiens alu"
  repeated (2 * n)
  IO.println ">TWO IUB ambiguity codes"
  let state ← randomSequence (3 * n) "acgtBDHKMNRSVWY".toUTF8 #[0.27, 0.12, 0.12, 0.27, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02] 42
  IO.println ">THREE Homo sapiens frequency"
  let _ ← randomSequence (5 * n) "acgt".toUTF8 #[0.3029549426680, 0.1979883004921, 0.1975473066391, 0.3015094502008] state
  Bench.finish
