import Std

unsafe def reversePrefix (p : ByteArray) (first last : USize) : ByteArray :=
  if first < last then
    let value := p.uget first lcProof
    let p := p.uset first (p.uget last lcProof) lcProof
    let p := p.uset last value lcProof
    reversePrefix p (first + 1) (last - 1)
  else p

unsafe def rotatePrefix (p : ByteArray) (i last : USize) (first : UInt8) : ByteArray :=
  if i < last then
    rotatePrefix (p.uset i (p.uget (i + 1) lcProof) lcProof) (i + 1) last first
  else p.uset last first lcProof

mutual
  unsafe def enumerating (n rank : USize) (p counts scratch : ByteArray)
      (remaining : UInt64) (positive : Bool) (checksum : Int64) (maximum : UInt32) : Int64 × UInt32 :=
    if rank > 1 then
      enumerating n (rank - 1) p (counts.uset (rank - 1) rank.toUInt8 lcProof) scratch remaining positive checksum maximum
    else
      flipping n p counts (p.copySlice 0 scratch 0 n.toNat) remaining positive checksum maximum 0

  unsafe def flipping (n : USize) (p counts work : ByteArray) (remaining : UInt64)
      (positive : Bool) (checksum : Int64) (maximum flips : UInt32) : Int64 × UInt32 :=
    let first := work.uget 0 lcProof
    if first == 0 then
      let value := flips.toUInt64.toInt64
      let checksum := if positive then checksum + value else checksum - value
      let maximum := max maximum flips
      if remaining == 1 then (checksum, maximum)
      else carrying n 1 p counts work (remaining - 1) (!positive) checksum maximum
    else
      flipping n p counts (reversePrefix work 0 first.toUSize) remaining positive checksum maximum (flips + 1)

  unsafe def carrying (n rank : USize) (p counts scratch : ByteArray)
      (remaining : UInt64) (positive : Bool) (checksum : Int64) (maximum : UInt32) : Int64 × UInt32 :=
    if rank == n then (checksum, maximum)
    else
      let p := rotatePrefix p 0 rank (p.uget 0 lcProof)
      let count := counts.uget rank lcProof - 1
      let counts := counts.uset rank count lcProof
      if count > 0 then enumerating n rank p counts scratch remaining positive checksum maximum
      else carrying n (rank + 1) p counts scratch remaining positive checksum maximum
end

unsafe def chunk (n : Nat) (factorials : Array Nat) (start count : Nat) : Int64 × UInt32 := Id.run do
  let mut p := ByteArray.mk ((Array.range n).map Nat.toUInt8)
  let mut counts := ByteArray.mk (Array.replicate n 0)
  let mut index := start
  for r in (List.range (n - 1)).reverse do
    let i := r + 1
    let digit := index / factorials[i]!
    index := index % factorials[i]!
    counts := counts.set! i (i + 1 - digit).toUInt8
    for _ in [:digit] do p := rotatePrefix p 0 i.toUSize (p.uget 0 lcProof)
  return enumerating n.toUSize 1 p counts (ByteArray.mk (Array.replicate n 0)) count.toUInt64 (start % 2 == 0) 0 0

unsafe def main (args : List String) : IO Unit := do
  let n := (args.headD "0").toNat!
  if n > 16 then throw (IO.userError "native permutation counters support n <= 16")
  let mut checksum : Int64 := 0
  let mut maximum : UInt32 := 0
  if n >= 2 then
    let mut factorials := #[1]
    for i in [1:n + 1] do factorials := factorials.push (factorials.back! * i)
    let total := factorials[n]!
    let workers := min 8 total
    let mut tasks := #[]
    for worker in [:workers] do
      let first := total * worker / workers
      let last := total * (worker + 1) / workers
      tasks := tasks.push (Task.spawn fun _ => chunk n factorials first (last - first))
    for task in tasks do
      let (sum, flips) := task.get
      checksum := checksum + sum
      maximum := max maximum flips
  IO.println s!"{checksum}\nPfannkuchen({n}) = {maximum}"
  (← IO.getStdout).flush
