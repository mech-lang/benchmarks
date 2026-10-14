/* Scala adaptation of the Computer Language Benchmarks Game FASTA program.
 * Java reference modified by Mehmet D. AKIN.
 * https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
 * See ../LICENSE.benchmarksgame.
 */
import java.io.BufferedOutputStream
import java.nio.charset.StandardCharsets

object Main {
  def main(args: Array[String]): Unit = {
    val n = args(0).toInt
    require(n >= 0 && n <= Int.MaxValue / 5)
    val output = new BufferedOutputStream(System.out, 65536)
    val alu = "GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGG" +
      "GAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGA" +
      "CCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAAT" +
      "ACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCA" +
      "GCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGG" +
      "AGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCC" +
      "AGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA"
    var randomState = 42

    def header(text: String): Unit =
      output.write((text + "\n").getBytes(StandardCharsets.US_ASCII))

    def randomRecord(symbols: String, probabilities: Array[Double], length: Int): Unit = {
      val cumulative = probabilities.clone()
      var i = 1
      while (i < cumulative.length) {
        cumulative(i) += cumulative(i - 1)
        i += 1
      }
      i = 0
      while (i < length) {
        randomState = (randomState * 3877 + 29573) % 139968
        val random = randomState.toDouble / 139968
        var index = 0
        while (index < cumulative.length - 1 && random >= cumulative(index)) index += 1
        output.write(symbols.charAt(index).toInt)
        i += 1
        if (i % 60 == 0 || i == length) output.write(10)
      }
    }

    header(">ONE Homo sapiens alu")
    var i = 0
    while (i < 2 * n) {
      output.write(alu.charAt(i % alu.length).toInt)
      i += 1
      if (i % 60 == 0 || i == 2 * n) output.write(10)
    }
    header(">TWO IUB ambiguity codes")
    randomRecord("acgtBDHKMNRSVWY",
      Array(0.27, 0.12, 0.12, 0.27, 0.02, 0.02, 0.02, 0.02, 0.02,
            0.02, 0.02, 0.02, 0.02, 0.02, 0.02), 3 * n)
    header(">THREE Homo sapiens frequency")
    randomRecord("acgt", Array(0.3029549426680, 0.1979883004921,
                              0.1975473066391, 0.3015094502008), 5 * n)
    output.flush()
  }
}
