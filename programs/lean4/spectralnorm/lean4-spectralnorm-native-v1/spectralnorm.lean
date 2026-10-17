import Common

def coefficient (i j : Nat) : Float :=
  1.0 / Float.ofNat ((i + j) * (i + j + 1) / 2 + i + 1)

def apply (n : Nat) (transpose : Bool) (x : FloatArray) : FloatArray := Id.run do
  let width := (n + 7) / 8
  let mut tasks := #[]
  for worker in [:8] do
    let first := min n (worker * width)
    let last := min n (first + width)
    tasks := tasks.push (Task.spawn fun _ => Id.run do
      let mut part := FloatArray.emptyWithCapacity (last - first)
      for i in [first:last] do
        let mut total := 0.0
        for j in [:n] do
          total := total + (if transpose then coefficient j i else coefficient i j) * x[j]!
        part := part.push total
      return part)
  let mut result := FloatArray.emptyWithCapacity n
  for task in tasks do
    let part := task.get
    for i in [:part.size] do
      result := result.push part[i]!
  return result

def step (n : Nat) (x : FloatArray) : FloatArray :=
  apply n true (apply n false x)

def main (args : List String) : IO Unit := do
  let n ← Bench.argument args
  let mut v := FloatArray.emptyWithCapacity n
  for _ in [:n] do v := v.push 1.0
  let mut u := v
  for _ in [:10] do
    v := step n u
    u := step n v
  let mut uv := 0.0
  let mut vv := 0.0
  for i in [:n] do
    uv := uv + u[i]! * v[i]!
    vv := vv + v[i]! * v[i]!
  IO.println (Bench.fixed (Float.sqrt (uv / vv)) 9)
  Bench.finish
