/* Scala implementation of the Computer Language Benchmarks Game workload.
 * Java reference contributors: James McIlree and Tagir Valeev.
 * Uses seven complete frequency maps and Scala's standard mutable.LongMap.
 * https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
 * See ../LICENSE.benchmarksgame.
 */
import java.io.{BufferedReader, ByteArrayOutputStream, InputStreamReader}
import java.nio.charset.StandardCharsets
import java.util.Locale
import scala.collection.mutable.LongMap

object Main {
  def code(symbol: Char): Int = symbol.toUpper match {
    case 'A' => 0
    case 'C' => 1
    case 'G' => 2
    case 'T' => 3
    case _ => throw new IllegalArgumentException(s"Invalid THREE nucleotide: $symbol")
  }

  def readSequence(): Array[Byte] = {
    val reader = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.ISO_8859_1), 65536)
    val sequence = new ByteArrayOutputStream
    var selected = false
    var found = false
    var line = reader.readLine()
    while (line != null) {
      if (line.startsWith(">")) {
        val identifier = line.substring(1).takeWhile(c => c != ' ' && c != '\t')
        selected = !found && identifier == "THREE"
        if (selected) found = true
      } else if (selected && !line.startsWith(";")) {
        var i = 0
        while (i < line.length) {
          sequence.write(code(line.charAt(i)))
          i += 1
        }
      }
      line = reader.readLine()
    }
    sequence.toByteArray
  }

  def table(sequence: Array[Byte], length: Int): LongMap[Int] = {
    val counts = LongMap.empty[Int]
    val mask = (1L << (2 * length)) - 1
    var key = 0L
    var i = 0
    while (i < sequence.length) {
      key = ((key << 2) | sequence(i).toLong) & mask
      if (i >= length - 1) counts.update(key, counts.getOrElse(key, 0) + 1)
      i += 1
    }
    counts
  }

  def decode(key: Long, length: Int): String = {
    val text = new Array[Char](length)
    var remaining = key
    var i = length - 1
    while (i >= 0) {
      text(i) = "ACGT".charAt((remaining & 3).toInt)
      remaining = remaining >>> 2
      i -= 1
    }
    new String(text)
  }

  def encode(text: String): Long = {
    var key = 0L
    text.foreach(c => key = (key << 2) | code(c).toLong)
    key
  }

  def main(args: Array[String]): Unit = {
    val sequence = readSequence()
    val lengths = Array(1, 2, 3, 4, 6, 12, 18)
    val queries = Array("GGT", "GGTA", "GGTATT", "GGTATTTTAATT", "GGTATTTTAATTTATAGT")
    lengths.indices.foreach { index =>
      val length = lengths(index)
      val counts = table(sequence, length)
      if (length <= 2) {
        val rows = counts.iterator.map { case (key, count) => (decode(key, length), count) }
          .toArray.sortBy { case (text, count) => (-count, text) }
        val total = math.max(0, sequence.length - length + 1)
        rows.foreach { case (text, count) =>
          System.out.printf(Locale.ROOT, "%s %.3f\n", text, Double.box(count * 100.0 / total))
        }
        println()
      } else {
        val query = queries(index - 2)
        println(s"${counts.getOrElse(encode(query), 0)}\t$query")
      }
    }
  }
}
