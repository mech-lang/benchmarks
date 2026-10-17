import Std

partial def inside (cr ci zr zi zr2 zi2 : Float) (remaining : UInt32) : Bool :=
  if zr2 + zi2 <= 4.0 then
    if remaining == 0 then true
    else
      let ziNext := 2.0 * zr * zi + ci
      let zrNext := zr2 - zi2 + cr
      inside cr ci zrNext ziNext (zrNext * zrNext) (ziNext * ziNext) (remaining - 1)
  else false

unsafe def rows (n first last : USize) (coordinates : FloatArray) : ByteArray := Id.run do
  let mut output := ByteArray.emptyWithCapacity ((last - first).toNat * ((n.toNat + 7) / 8))
  let denominator := n.toUInt64.toFloat
  let mut y := first
  while y < last do
    let ci := 2.0 * y.toUInt64.toFloat / denominator - 1.0
    let mut byte : UInt8 := 0
    let mut used : UInt8 := 0
    let mut x : USize := 0
    while x < n do
      let cr := coordinates.uget x lcProof
      byte := (byte <<< 1) ||| (if inside cr ci 0 0 0 0 50 then 1 else 0)
      used := used + 1
      if used == 8 then
        output := output.push byte
        byte := 0
        used := 0
      x := x + 1
    if used != 0 then output := output.push (byte <<< (8 - used))
    y := y + 1
  return output

unsafe def main (args : List String) : IO Unit := do
  let n := (args.headD "0").toNat!
  IO.print s!"P4\n{n} {n}\n"
  let mut coordinates := FloatArray.emptyWithCapacity n
  for x in [:n] do
    coordinates := coordinates.push (2.0 * Float.ofNat x / Float.ofNat n - 1.5)
  let width := (n + 7) / 8
  let mut tasks := #[]
  for worker in [:8] do
    let first := min n (worker * width)
    let last := min n (first + width)
    tasks := tasks.push (Task.spawn fun _ => rows n.toUSize first.toUSize last.toUSize coordinates)
  for task in tasks do (← IO.getStdout).write task.get
  (← IO.getStdout).flush
