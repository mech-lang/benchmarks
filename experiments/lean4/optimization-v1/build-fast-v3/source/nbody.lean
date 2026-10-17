import Std

@[extern "lean_bench_fixed"]
opaque fixed (value : Float) (digits : UInt32) : String

def solarMass : Float := 4.0 * 3.141592653589793 * 3.141592653589793
def days : Float := 365.24

def initial : FloatArray := Id.run do
  let values : Array Float := #[
    0, 0, 0, 0, 0, 0, solarMass,
    4.84143144246472090, -1.16032004402742839, -0.103622044471123109,
    0.00166007664274403694 * days, 0.00769901118419740425 * days, -0.0000690460016972063023 * days, 0.000954791938424326609 * solarMass,
    8.34336671824457987, 4.12479856412430479, -0.403523417114321381,
    -0.00276742510726862411 * days, 0.00499852801234917238 * days, 0.0000230417297573763929 * days, 0.000285885980666130812 * solarMass,
    12.8943695621391310, -15.1111514016986312, -0.223307578892655734,
    0.00296460137564761618 * days, 0.00237847173959480950 * days, -0.0000296589568540237556 * days, 0.0000436624404335156298 * solarMass,
    15.3796971148509165, -25.9193146099879641, 0.179258772950371181,
    0.00268067772490389322 * days, 0.00162824170038242295 * days, -0.0000951592254519715870 * days, 0.0000515138902046611451 * solarMass]
  let mut bodies := FloatArray.emptyWithCapacity 35
  for value in values do bodies := bodies.push value
  let mut px := 0.0
  let mut py := 0.0
  let mut pz := 0.0
  for i in [:5] do
    px := px + bodies[7 * i + 3]! * bodies[7 * i + 6]!
    py := py + bodies[7 * i + 4]! * bodies[7 * i + 6]!
    pz := pz + bodies[7 * i + 5]! * bodies[7 * i + 6]!
  bodies := bodies.set! 3 (-px / solarMass)
  bodies := bodies.set! 4 (-py / solarMass)
  bodies := bodies.set! 5 (-pz / solarMass)
  return bodies

def energy (b : FloatArray) : Float := Id.run do
  let mut value := 0.0
  for i in [:5] do
    let a := 7 * i
    value := value + 0.5 * b[a + 6]! * (b[a + 3]! * b[a + 3]! + b[a + 4]! * b[a + 4]! + b[a + 5]! * b[a + 5]!)
    for j in [i + 1:5] do
      let c := 7 * j
      let dx := b[a]! - b[c]!
      let dy := b[a + 1]! - b[c + 1]!
      let dz := b[a + 2]! - b[c + 2]!
      value := value - b[a + 6]! * b[c + 6]! / Float.sqrt (dx * dx + dy * dy + dz * dz)
  return value

@[inline] unsafe def bodyAt (b : @& FloatArray) (i : USize) : Float :=
  b.uget i lcProof

@[inline] unsafe def bodyPut (b : FloatArray) (i : USize) (value : Float) : FloatArray :=
  b.uset i value lcProof

unsafe partial def pairs (a j : USize) (x y z mass : Float) (b : FloatArray) : FloatArray :=
  if j < 5 then
    let c := 7 * j
    let dx := x - bodyAt b c
    let dy := y - bodyAt b (c + 1)
    let dz := z - bodyAt b (c + 2)
    let squared := dx * dx + dy * dy + dz * dz
    let magnitude := 0.01 / (squared * Float.sqrt squared)
    let mj := bodyAt b (c + 6) * magnitude
    let mi := mass * magnitude
    let b := bodyPut b (a + 3) (bodyAt b (a + 3) - dx * mj)
    let b := bodyPut b (a + 4) (bodyAt b (a + 4) - dy * mj)
    let b := bodyPut b (a + 5) (bodyAt b (a + 5) - dz * mj)
    let b := bodyPut b (c + 3) (bodyAt b (c + 3) + dx * mi)
    let b := bodyPut b (c + 4) (bodyAt b (c + 4) + dy * mi)
    let b := bodyPut b (c + 5) (bodyAt b (c + 5) + dz * mi)
    pairs a (j + 1) x y z mass b
  else b

unsafe partial def velocities (i : USize) (b : FloatArray) : FloatArray :=
  if i < 5 then
    let a := 7 * i
    let next := pairs a (i + 1) (bodyAt b a) (bodyAt b (a + 1)) (bodyAt b (a + 2)) (bodyAt b (a + 6)) b
    velocities (i + 1) next
  else b

unsafe partial def positions (i : USize) (b : FloatArray) : FloatArray :=
  if i < 5 then
    let a := 7 * i
    let b := bodyPut b a (bodyAt b a + 0.01 * bodyAt b (a + 3))
    let b := bodyPut b (a + 1) (bodyAt b (a + 1) + 0.01 * bodyAt b (a + 4))
    let b := bodyPut b (a + 2) (bodyAt b (a + 2) + 0.01 * bodyAt b (a + 5))
    positions (i + 1) b
  else b

unsafe def advance (b : FloatArray) : FloatArray :=
  positions 0 (velocities 0 b)

unsafe def main (args : List String) : IO Unit := do
  let n := (args.headD "0").toNat!
  let mut bodies := initial
  IO.println (fixed (energy bodies) 9)
  for _ in [:n] do bodies := advance bodies
  IO.println (fixed (energy bodies) 9)
  (← IO.getStdout).flush
