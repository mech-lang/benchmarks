/* Scala adaptation of the Computer Language Benchmarks Game program
 * contributed by Francois Green. Pattern matching uses java.util.regex.
 * https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
 * See ../LICENSE.benchmarksgame.
 */
import java.nio.charset.StandardCharsets
import java.util.concurrent.{Callable, Executors}
import java.util.regex.Pattern

object Main {
  def main(args: Array[String]): Unit = {
    val input = new String(System.in.readAllBytes(), StandardCharsets.ISO_8859_1)
    val sequence = Pattern.compile(">[^\\n]*\\n|\\n").matcher(input).replaceAll("")
    val variants = Array(
      "agggtaaa|tttaccct", "[cgt]gggtaaa|tttaccc[acg]",
      "a[act]ggtaaa|tttacc[agt]t", "ag[act]gtaaa|tttac[agt]ct",
      "agg[act]taaa|ttta[agt]cct", "aggg[acg]aaa|ttt[cgt]ccct",
      "agggt[cgt]aa|tt[acg]accct", "agggta[cgt]a|t[acg]taccct",
      "agggtaa[cgt]|[acg]ttaccct")
    val pool = Executors.newFixedThreadPool(math.min(8, Runtime.getRuntime.availableProcessors()))
    try {
      val counts = variants.map { pattern =>
        pool.submit(new Callable[Long] {
          def call(): Long = {
            val matches = Pattern.compile(pattern).matcher(sequence)
            var count = 0L
            while (matches.find()) count += 1
            count
          }
        })
      }
      val replacements = pool.submit(new Callable[Int] {
        def call(): Int = {
          val rules = Array(
            ("tHa[Nt]", "<4>"), ("aND|caN|Ha[DS]|WaS", "<3>"),
            ("a[NSt]|BY", "<2>"), ("<[^>]*>", "|"), ("\\|[^|][^|]*\\|", "-"))
          var result = sequence
          rules.foreach { case (pattern, replacement) =>
            result = Pattern.compile(pattern).matcher(result).replaceAll(replacement)
          }
          result.length
        }
      })
      variants.indices.foreach(i => println(s"${variants(i)} ${counts(i).get()}"))
      println()
      println(input.length)
      println(sequence.length)
      println(replacements.get())
    } finally pool.shutdown()
  }
}
