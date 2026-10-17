import Std

@[extern "lean_bench_fixed"]
opaque fixed (value : Float) (digits : UInt32) : String

@[inline] def coefficient (i j : USize) : Float :=
  1 / ((i + j) * (i + j + 1) / 2 + i + 1).toUInt64.toFloat

unsafe def dot (n i j : USize) (transpose : Bool) (x : @& FloatArray) (total : Float) : Float :=
  if j < n then
    let a := if transpose then coefficient j i else coefficient i j
    dot n i (j + 1) transpose x (total + a * x.uget j lcProof)
  else total

unsafe def apply (n : Nat) (transpose : Bool) (x : FloatArray) : FloatArray := Id.run do
  let width := (n + 7) / 8
  let mut tasks := #[]
  for worker in [:8] do
    let first := min n (worker * width)
    let last := min n (first + width)
    tasks := tasks.push (Task.spawn fun _ => Id.run do
      let mut part := FloatArray.emptyWithCapacity (last - first)
      let mut i := first.toUSize
      while i < last.toUSize do
        part := part.push (dot n.toUSize i 0 transpose x 0)
        i := i + 1
      return part)
  return tasks.foldl (fun output task => task.get.foldl (·.push ·) output) (FloatArray.emptyWithCapacity n)

unsafe def step (n : Nat) (x : FloatArray) : FloatArray :=
  apply n true (apply n false x)

unsafe def main (args : List String) : IO Unit := do
  let n := (args.headD "0").toNat!
  let mut v := (List.replicate n 1.0).toFloatArray
  let mut u := v
  for _ in [:10] do
    v := step n u
    u := step n v
  let mut uv := 0.0
  let mut vv := 0.0
  for i in [:n] do
    uv := uv + u[i]! * v[i]!
    vv := vv + v[i]! * v[i]!
  IO.println (fixed (Float.sqrt (uv / vv)) 9)
  (← IO.getStdout).flush
