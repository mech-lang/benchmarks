import Std

@[extern "lean_bench_fixed"]
opaque fixed (value : Float) (digits : UInt32) : String

abbrev Key := UInt64

@[inline] def mapKey (key : UInt64) : Key := key
@[inline] def wordKey (key : Key) : UInt64 := key

def code (byte : UInt8) : Option UInt8 :=
  match byte &&& 223 with
  | 65 => some 0
  | 67 => some 1
  | 71 => some 2
  | 84 => some 3
  | _ => none

def thirdHeader (line : ByteArray) : Bool :=
  line.size >= 6 && line.extract 0 6 == ">THREE".toUTF8 &&
    (line.size == 6 || line[6]! == 32 || line[6]! == 9)

def appendSequence (sequence line : ByteArray) : IO ByteArray := do
  let mut result := sequence
  for byte in line do
    match code byte with
    | some value => result := result.push value
    | none => throw (IO.userError "invalid nucleotide in THREE record")
  return result

def readSequence : IO ByteArray := do
  let input ← IO.getStdin
  let mut sequence := ByteArray.empty
  let mut line := ByteArray.empty
  let mut selected := false
  let mut finished := false
  while !finished do
    let block ← input.read 65536
    let eof := block.isEmpty
    let bytes := if eof then ByteArray.empty.push 10 else block
    for byte in bytes do
      if finished then break
      if byte == 10 || byte == 13 then
        if !line.isEmpty then
          if line[0]! == 62 then
            if selected then finished := true
            else selected := thirdHeader line
          else if selected && line[0]! != 59 then
            sequence ← appendSequence sequence line
        line := ByteArray.empty
      else
        line := line.push byte
    if eof then finished := true
  return sequence

def histogram (sequence : ByteArray) (width : Nat) : Std.HashMap Key Nat := Id.run do
  let mask : UInt64 := (1 <<< (2 * width).toUInt64) - 1
  let mut counts : Std.HashMap Key Nat := Std.HashMap.emptyWithCapacity
  let mut key : UInt64 := 0
  for i in [:sequence.size] do
    key := ((key <<< 2) ||| sequence[i]!.toUInt64) &&& mask
    if i + 1 >= width then
      counts := counts.alter (mapKey key) (fun previous => some (previous.getD 0 + 1))
  return counts

def decode (key : Key) (width : Nat) : String := Id.run do
  let mut text := ""
  let mut value := wordKey key
  for _ in [:width] do
    text := String.singleton ("ACGT".toList[(value % 4).toNat]!) ++ text
    value := value / 4
  return text

def frequencies (sequence : ByteArray) (width : Nat) : IO Unit := do
  let counts := histogram sequence width
  let total := counts.fold (fun sum _ count => sum + count) 0
  let rows := counts.toArray.qsort (fun a b => a.2 > b.2 || (a.2 == b.2 && a.1 < b.1))
  for (key, count) in rows do
    IO.println s!"{decode key width} {fixed (100.0 * Float.ofNat count / Float.ofNat total) 3}"
  IO.println ""

def queryKey (query : String) : Key := Id.run do
  let mut key : UInt64 := 0
  for byte in query.toUTF8 do
    key := (key <<< 2) ||| (code byte).get!.toUInt64
  return mapKey key

def main : IO Unit := do
  let sequence ← readSequence
  frequencies sequence 1
  frequencies sequence 2
  for query in #["GGT", "GGTA", "GGTATT", "GGTATTTTAATT", "GGTATTTTAATTTATAGT"] do
    let counts := histogram sequence query.utf8ByteSize
    IO.println s!"{counts.getD (queryKey query) 0}\t{query}"
  (← IO.getStdout).flush
