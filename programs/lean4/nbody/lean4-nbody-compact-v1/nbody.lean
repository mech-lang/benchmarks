import Std

@[extern "lean_bench_fixed"]
opaque fixed (value : Float) (digits : UInt32) : String

structure Vec3 where
  x : Float
  y : Float
  z : Float
  deriving Inhabited

@[inline] instance : Add Vec3 := ⟨fun a b => ⟨a.x + b.x, a.y + b.y, a.z + b.z⟩⟩
@[inline] instance : Sub Vec3 := ⟨fun a b => ⟨a.x - b.x, a.y - b.y, a.z - b.z⟩⟩
@[inline] def scale (k : Float) (v : Vec3) : Vec3 := ⟨v.x * k, v.y * k, v.z * k⟩
@[inline] def squared (v : Vec3) : Float := v.x * v.x + v.y * v.y + v.z * v.z

structure Body where
  position : Vec3
  velocity : Vec3
  mass : Float
  deriving Inhabited

def solarMass : Float := 4.0 * 3.141592653589793 * 3.141592653589793
def days : Float := 365.24

def initial : Array Body := #[
  ⟨⟨0, 0, 0⟩, ⟨0, 0, 0⟩, solarMass⟩,
  ⟨⟨4.84143144246472090, -1.16032004402742839, -0.103622044471123109⟩,
    scale days ⟨0.00166007664274403694, 0.00769901118419740425, -0.0000690460016972063023⟩, 0.000954791938424326609 * solarMass⟩,
  ⟨⟨8.34336671824457987, 4.12479856412430479, -0.403523417114321381⟩,
    scale days ⟨-0.00276742510726862411, 0.00499852801234917238, 0.0000230417297573763929⟩, 0.000285885980666130812 * solarMass⟩,
  ⟨⟨12.8943695621391310, -15.1111514016986312, -0.223307578892655734⟩,
    scale days ⟨0.00296460137564761618, 0.00237847173959480950, -0.0000296589568540237556⟩, 0.0000436624404335156298 * solarMass⟩,
  ⟨⟨15.3796971148509165, -25.9193146099879641, 0.179258772950371181⟩,
    scale days ⟨0.00268067772490389322, 0.00162824170038242295, -0.0000951592254519715870⟩, 0.0000515138902046611451 * solarMass⟩]

def offsetMomentum (b : Array Body) : Array Body :=
  let p := b.foldl (fun sum body => sum + scale body.mass body.velocity) (⟨0, 0, 0⟩ : Vec3)
  b.modify 0 fun sun => { sun with velocity := ⟨-p.x / solarMass, -p.y / solarMass, -p.z / solarMass⟩ }

def energy (b : Array Body) : Float := Id.run do
  let mut e := 0.0
  for i in [:b.size] do
    let a := b[i]!
    e := e + 0.5 * a.mass * squared a.velocity
    for j in [i + 1:b.size] do
      let c := b[j]!
      e := e - a.mass * c.mass / Float.sqrt (squared (a.position - c.position))
  return e

def advance (input : Array Body) : Array Body := Id.run do
  let mut b := input
  for i in [:b.size] do
    for j in [i + 1:b.size] do
      let delta := b[i]!.position - b[j]!.position
      let distance := squared delta
      let magnitude := 0.01 / (distance * Float.sqrt distance)
      let mi := b[i]!.mass * magnitude
      let mj := b[j]!.mass * magnitude
      b := b.modify i fun body => { body with velocity := body.velocity - scale mj delta }
      b := b.modify j fun body => { body with velocity := body.velocity + scale mi delta }
  return b.map fun body => { body with position := body.position + scale 0.01 body.velocity }

def main (args : List String) : IO Unit := do
  let bodies := offsetMomentum initial
  IO.println (fixed (energy bodies) 9)
  let final := Nat.repeat advance (args.headD "0").toNat! bodies
  IO.println (fixed (energy final) 9)
  (← IO.getStdout).flush
