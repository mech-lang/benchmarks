/* Scala spigot adaptation of the Computer Language Benchmarks Game program
 * contributed by Isaac Gouy. Both candidate digit extractions are retained.
 * https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
 * See ../LICENSE.benchmarksgame.
 */
object Main {
  def main(args: Array[String]): Unit = {
    val n = args(0).toInt
    require(n >= 0)
    var q = BigInt(1)
    var r = BigInt(0)
    var t = BigInt(1)
    var k = BigInt(0)
    var emitted = 0
    val line = new StringBuilder
    while (emitted < n) {
      val first = (3 * q + r) / t
      val second = (4 * q + r) / t
      if (first == second) {
        line.append(first.toInt)
        emitted += 1
        q *= 10
        r = 10 * (r - first * t)
        if (emitted % 10 == 0 || emitted == n) {
          while (line.length < 10) line.append(' ')
          println(s"$line\t:$emitted")
          line.clear()
        }
      } else {
        k += 1
        r = q * (4 * k + 2) + r * (2 * k + 1)
        q *= k
        t *= 2 * k + 1
      }
    }
  }
}
