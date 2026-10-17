import Common

def digits (n : Nat) : String := Id.run do
  let mut q : Int := 1
  let mut r : Int := 0
  let mut t : Int := 1
  let mut k : Int := 1
  let mut emitted := 0
  let mut line := ""
  let mut output := ""
  while emitted < n do
    -- Both independent spigot extractions must agree before emission.
    let a := (3 * q + r) / t
    let b := (4 * q + r) / t
    if a == b then
      line := line ++ toString a
      emitted := emitted + 1
      q := 10 * q
      r := 10 * (r - a * t)
      if emitted % 10 == 0 || emitted == n then
        output := output ++ line ++ String.ofList (List.replicate (10 - line.length) ' ') ++ s!"\t:{emitted}\n"
        line := ""
    else
      let odd := 2 * k + 1
      r := (2 * q + r) * odd
      q := q * k
      t := t * odd
      k := k + 1
  return output

def main (args : List String) : IO Unit := do
  IO.print (digits (← Bench.argument args))
  Bench.finish
