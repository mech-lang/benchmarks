import Common

def code (byte : UInt8) : Option UInt8 :=
  match byte &&& 223 with
  | 65 => some 0
  | 67 => some 1
  | 71 => some 2
  | 84 => some 3
  | _ => none

def readSequence (input : ByteArray) : IO ByteArray := do
  let mut selected := false
  let mut finished := false
  let mut position := 0
  let mut sequence := ByteArray.empty
  while position < input.size && !finished do
    let first := position
    while position < input.size && input[position]! != 10 && input[position]! != 13 do
      position := position + 1
    let last := position
    position := position + 1
    if first < last then
      if input[first]! == 62 then
        if selected then finished := true
        else
          selected := last - first >= 6 && input.extract first (first + 6) == ">THREE".toUTF8 &&
            (last - first == 6 || input[first + 6]! == 32 || input[first + 6]! == 9)
      else if selected && input[first]! != 59 then
        for i in [first:last] do
          match code input[i]! with
          | some value => sequence := sequence.push value
          | none => throw (IO.userError "invalid nucleotide in THREE record")
  return sequence

def histogram (sequence : ByteArray) (width : Nat) : Array Nat := Id.run do
  let size := 4 ^ width
  let mask := size - 1
  let mut counts := Array.replicate size 0
  let mut key := 0
  for i in [:sequence.size] do
    key := (4 * key + sequence[i]!.toNat) % (mask + 1)
    if i + 1 >= width then counts := counts.set! key (counts[key]! + 1)
  return counts

def decode (key width : Nat) : String := Id.run do
  let mut text := ""
  let mut value := key
  for _ in [:width] do
    text := String.singleton ("ACGT".toList[value % 4]!) ++ text
    value := value / 4
  return text

def frequencies (sequence : ByteArray) (width : Nat) : IO Unit := do
  let counts := histogram sequence width
  let mut rows := #[]
  let mut total := 0
  for key in [:counts.size] do
    total := total + counts[key]!
    if counts[key]! > 0 then rows := rows.push (key, counts[key]!)
  rows := rows.qsort (fun a b => a.2 > b.2 || (a.2 == b.2 && a.1 < b.1))
  for (key, count) in rows do
    IO.println s!"{decode key width} {Bench.fixed (100.0 * Float.ofNat count / Float.ofNat total) 3}"
  IO.println ""

def occurrences (sequence : ByteArray) (query : String) : Nat := Id.run do
  let width := query.utf8ByteSize
  let mask : UInt64 := (1 <<< (2 * width).toUInt64) - 1
  let mut wanted : UInt64 := 0
  for byte in query.toUTF8 do wanted := 4 * wanted + (code byte).get!.toUInt64
  let mut key : UInt64 := 0
  let mut count := 0
  for i in [:sequence.size] do
    key := ((key <<< 2) ||| sequence[i]!.toUInt64) &&& mask
    if i + 1 >= width && key == wanted then count := count + 1
  return count

def main : IO Unit := do
  let sequence ← readSequence (← Bench.readAll)
  frequencies sequence 1
  frequencies sequence 2
  for query in #["GGT", "GGTA", "GGTATT", "GGTATTTTAATT", "GGTATTTTAATTTATAGT"] do
    IO.println s!"{occurrences sequence query}\t{query}"
  Bench.finish
