/* Scala adaptation of the Computer Language Benchmarks Game program.
 * Contributed by Mark C. Lewis; double[] layout by Han Kai.
 * https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
 * See ../LICENSE.benchmarksgame.
 */
import java.util.Locale

object Main {
  final class SystemState {
    private val solarMass = 4.0 * math.Pi * math.Pi
    private val daysPerYear = 365.24
    private val bodies = Array[Double](
      0, 0, 0, 0, 0, 0, solarMass, 0,
      4.84143144246472090, -1.16032004402742839, -1.03622044471123109e-1,
      1.66007664274403694e-3 * daysPerYear, 7.69901118419740425e-3 * daysPerYear,
      -6.90460016972063023e-5 * daysPerYear, 9.54791938424326609e-4 * solarMass, 0,
      8.34336671824457987, 4.12479856412430479, -4.03523417114321381e-1,
      -2.76742510726862411e-3 * daysPerYear, 4.99852801234917238e-3 * daysPerYear,
      2.30417297573763929e-5 * daysPerYear, 2.85885980666130812e-4 * solarMass, 0,
      1.28943695621391310e1, -1.51111514016986312e1, -2.23307578892655734e-1,
      2.96460137564761618e-3 * daysPerYear, 2.37847173959480950e-3 * daysPerYear,
      -2.96589568540237556e-5 * daysPerYear, 4.36624404335156298e-5 * solarMass, 0,
      1.53796971148509165e1, -2.59193146099879641e1, 1.79258772950371181e-1,
      2.68067772490389322e-3 * daysPerYear, 1.62824170038242295e-3 * daysPerYear,
      -9.51592254519715870e-5 * daysPerYear, 5.15138902046611451e-5 * solarMass, 0)

    def offsetMomentum(): Unit = {
      var px = 0.0
      var py = 0.0
      var pz = 0.0
      var i = 0
      while (i < 40) {
        px += bodies(i + 3) * bodies(i + 6)
        py += bodies(i + 4) * bodies(i + 6)
        pz += bodies(i + 5) * bodies(i + 6)
        i += 8
      }
      bodies(3) = -px / solarMass
      bodies(4) = -py / solarMass
      bodies(5) = -pz / solarMass
    }

    def advance(dt: Double): Unit = {
      var i = 0
      while (i < 40) {
        var j = i + 8
        while (j < 40) {
          val dx = bodies(i) - bodies(j)
          val dy = bodies(i + 1) - bodies(j + 1)
          val dz = bodies(i + 2) - bodies(j + 2)
          val squared = dx * dx + dy * dy + dz * dz
          val magnitude = dt / (squared * math.sqrt(squared))
          val otherMass = bodies(j + 6)
          bodies(i + 3) -= dx * otherMass * magnitude
          bodies(i + 4) -= dy * otherMass * magnitude
          bodies(i + 5) -= dz * otherMass * magnitude
          val mass = bodies(i + 6)
          bodies(j + 3) += dx * mass * magnitude
          bodies(j + 4) += dy * mass * magnitude
          bodies(j + 5) += dz * mass * magnitude
          j += 8
        }
        i += 8
      }
      i = 0
      while (i < 40) {
        bodies(i) += dt * bodies(i + 3)
        bodies(i + 1) += dt * bodies(i + 4)
        bodies(i + 2) += dt * bodies(i + 5)
        i += 8
      }
    }

    def energy(): Double = {
      var result = 0.0
      var i = 0
      while (i < 40) {
        val vx = bodies(i + 3)
        val vy = bodies(i + 4)
        val vz = bodies(i + 5)
        val mass = bodies(i + 6)
        result += 0.5 * mass * (vx * vx + vy * vy + vz * vz)
        var j = i + 8
        while (j < 40) {
          val dx = bodies(i) - bodies(j)
          val dy = bodies(i + 1) - bodies(j + 1)
          val dz = bodies(i + 2) - bodies(j + 2)
          result -= mass * bodies(j + 6) / math.sqrt(dx * dx + dy * dy + dz * dz)
          j += 8
        }
        i += 8
      }
      result
    }
  }

  def main(args: Array[String]): Unit = {
    val n = args(0).toInt
    require(n >= 0)
    val state = new SystemState
    state.offsetMomentum()
    System.out.printf(Locale.ROOT, "%.9f\n", Double.box(state.energy()))
    var step = 0
    while (step < n) {
      state.advance(0.01)
      step += 1
    }
    System.out.printf(Locale.ROOT, "%.9f\n", Double.box(state.energy()))
  }
}
