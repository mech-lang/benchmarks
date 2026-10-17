import Std

partial def inside (cr ci zr zi zr2 zi2 : Float) (remaining : UInt32) : Bool :=
  if zr2 + zi2 <= 4 then
    if remaining == 0 then true
    else
      let ziNext := 2 * zr * zi + ci
      let zrNext := zr2 - zi2 + cr
      inside cr ci zrNext ziNext (zrNext * zrNext) (ziNext * ziNext) (remaining - 1)
  else false

def rows (n first last : Nat) : ByteArray := Id.run do
  let mut output := ByteArray.emptyWithCapacity ((last - first) * ((n + 7) / 8))
  for y in [first:last] do
    let ci := 2.0 * Float.ofNat y / Float.ofNat n - 1.0
    let mut byte : UInt8 := 0
    let mut used := 0
    for x in [:n] do
      let cr := 2.0 * Float.ofNat x / Float.ofNat n - 1.5
      byte := (byte <<< 1) ||| (if inside cr ci 0 0 0 0 50 then 1 else 0)
      used := used + 1
      if used == 8 then
        output := output.push byte
        byte := 0
        used := 0
    if used != 0 then output := output.push (byte <<< (8 - used).toUInt8)
  return output

def main (args : List String) : IO Unit := do
  let n := (args.headD "0").toNat!
  IO.print s!"P4\n{n} {n}\n"
  let width := (n + 7) / 8
  let mut tasks := #[]
  for worker in [:8] do
    let first := min n (worker * width)
    let last := min n (first + width)
    tasks := tasks.push (Task.spawn fun _ => rows n first last)
  for task in tasks do (← IO.getStdout).write task.get
  (← IO.getStdout).flush
