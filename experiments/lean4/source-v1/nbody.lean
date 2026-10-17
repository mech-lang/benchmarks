import Common

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

def advance (input : FloatArray) : FloatArray := Id.run do
  let mut b := input
  for i in [:5] do
    for j in [i + 1:5] do
      let a := 7 * i
      let c := 7 * j
      let dx := b[a]! - b[c]!
      let dy := b[a + 1]! - b[c + 1]!
      let dz := b[a + 2]! - b[c + 2]!
      let squared := dx * dx + dy * dy + dz * dz
      let magnitude := 0.01 / (squared * Float.sqrt squared)
      let mj := b[c + 6]! * magnitude
      let mi := b[a + 6]! * magnitude
      b := b.set! (a + 3) (b[a + 3]! - dx * mj)
      b := b.set! (a + 4) (b[a + 4]! - dy * mj)
      b := b.set! (a + 5) (b[a + 5]! - dz * mj)
      b := b.set! (c + 3) (b[c + 3]! + dx * mi)
      b := b.set! (c + 4) (b[c + 4]! + dy * mi)
      b := b.set! (c + 5) (b[c + 5]! + dz * mi)
  for i in [:5] do
    for axis in [:3] do
      let p := 7 * i + axis
      b := b.set! p (b[p]! + 0.01 * b[p + 3]!)
  return b

def main (args : List String) : IO Unit := do
  let n ← Bench.argument args
  let mut bodies := initial
  IO.println (Bench.fixed (energy bodies) 9)
  for _ in [:n] do bodies := advance bodies
  IO.println (Bench.fixed (energy bodies) 9)
  Bench.finish
