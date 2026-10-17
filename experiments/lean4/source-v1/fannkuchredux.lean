import Common

def fannkuch (n : Nat) : Int × Nat := Id.run do
  if n < 2 then return (0, 0)
  let mut permutation := (List.range n).toArray
  let mut counts := Array.replicate n 0
  let mut rank := n
  let mut index := 0
  let mut checksum : Int := 0
  let mut maximum := 0
  let mut done := false
  while !done do
    while rank != 1 do
      counts := counts.set! (rank - 1) rank
      rank := rank - 1
    let mut flips := 0
    if permutation[0]! != 0 then
      let mut work := permutation
      while work[0]! != 0 do
        let k := work[0]!
        let mut a := 0
        let mut b := k
        while a < b do
          let value := work[a]!
          work := work.set! a work[b]!
          work := work.set! b value
          a := a + 1
          b := b - 1
        flips := flips + 1
    maximum := max maximum flips
    checksum := checksum + (if index % 2 == 0 then Int.ofNat flips else -(Int.ofNat flips))
    let mut carrying := true
    while carrying do
      if rank == n then
        done := true
        carrying := false
      else
        let first := permutation[0]!
        for i in [:rank] do permutation := permutation.set! i permutation[i + 1]!
        permutation := permutation.set! rank first
        counts := counts.set! rank (counts[rank]! - 1)
        if counts[rank]! > 0 then carrying := false else rank := rank + 1
    index := index + 1
  return (checksum, maximum)

def main (args : List String) : IO Unit := do
  let n ← Bench.argument args
  let (checksum, maximum) := fannkuch n
  IO.println s!"{checksum}\nPfannkuchen({n}) = {maximum}"
  Bench.finish
