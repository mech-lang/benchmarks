import Std

def complements : ByteArray := Id.run do
  let symbols := "ACBDGHKMNSRUTWVYacbdghkmnsrutwvy".toUTF8
  let values := "TGVHCDMKNSYAAWBRTGVHCDMKNSYAAWBR".toUTF8
  let mut table := ByteArray.empty
  for _ in [:256] do table := table.push 0
  for i in [:symbols.size] do table := table.set! symbols[i]!.toNat values[i]!
  return table

def emitRecord (header sequence : ByteArray) : IO Unit := do
  (← IO.getStdout).write header
  (← IO.getStdout).write (ByteArray.empty.push 10)
  let mut output := ByteArray.emptyWithCapacity 65575
  let mut remaining := sequence.size
  let mut column := 0
  while remaining > 0 do
    remaining := remaining - 1
    let original := sequence[remaining]!
    let mapped := complements[original.toNat]!
    if mapped == 0 then throw (IO.userError s!"Invalid IUPAC byte: {original.toNat}")
    output := output.push mapped
    column := column + 1
    if column == 60 then
      output := output.push 10
      column := 0
    if output.size >= 65536 then
      (← IO.getStdout).write output
      output := ByteArray.emptyWithCapacity 65575
  if column != 0 then output := output.push 10
  (← IO.getStdout).write output

def run : IO Unit := do
  let input ← (← IO.getStdin).readBinToEnd
  let mut header : Option ByteArray := none
  let mut sequence := ByteArray.empty
  let mut position := 0
  while position < input.size do
    let first := position
    while position < input.size && input[position]! != 10 && input[position]! != 13 do
      position := position + 1
    let last := position
    position := position + 1
    if first < last then
      if input[first]! == 62 then
        if let some previous := header then emitRecord previous sequence
        header := some (input.extract first last)
        sequence := ByteArray.empty
      else if header.isSome && input[first]! != 59 then
        sequence := sequence ++ input.extract first last
  if let some previous := header then emitRecord previous sequence
  (← IO.getStdout).flush

def main : IO UInt32 := do
  try
    run
    return 0
  catch error =>
    (← IO.getStdout).flush
    IO.eprintln error.toString
    return 1
