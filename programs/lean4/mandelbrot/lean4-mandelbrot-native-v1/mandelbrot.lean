import Common

def rows (n first last : Nat) : ByteArray := Id.run do
  let mut output := ByteArray.emptyWithCapacity ((last - first) * ((n + 7) / 8))
  for y in [first:last] do
    let ci := 2.0 * Float.ofNat y / Float.ofNat n - 1.0
    let mut byte : UInt8 := 0
    let mut used := 0
    for x in [:n] do
      let cr := 2.0 * Float.ofNat x / Float.ofNat n - 1.5
      let mut zr := 0.0
      let mut zi := 0.0
      let mut zr2 := 0.0
      let mut zi2 := 0.0
      let mut iteration := 0
      while iteration < 50 && zr2 + zi2 <= 4.0 do
        zi := 2.0 * zr * zi + ci
        zr := zr2 - zi2 + cr
        zr2 := zr * zr
        zi2 := zi * zi
        iteration := iteration + 1
      byte := (byte <<< 1) ||| (if zr2 + zi2 <= 4.0 then 1 else 0)
      used := used + 1
      if used == 8 then
        output := output.push byte
        byte := 0
        used := 0
    if used != 0 then output := output.push (byte <<< (8 - used).toUInt8)
  return output

def main (args : List String) : IO Unit := do
  let n ← Bench.argument args
  IO.print s!"P4\n{n} {n}\n"
  let width := (n + 7) / 8
  let mut tasks := #[]
  for worker in [:8] do
    let first := min n (worker * width)
    let last := min n (first + width)
    tasks := tasks.push (Task.spawn fun _ => rows n first last)
  for task in tasks do Bench.writeBytes task.get
  Bench.finish
