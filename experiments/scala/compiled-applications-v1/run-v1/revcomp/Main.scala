/* Reverse-complement workload from the Computer Language Benchmarks Game.
 * New Scala record parser; IUPAC mapping follows the retained workload contract.
 * Java reference contributors: Leonhard Holz and Anthony Donnefort.
 * https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
 * See ../LICENSE.benchmarksgame.
 */
import java.io.{BufferedOutputStream, BufferedReader, InputStreamReader}
import java.nio.charset.StandardCharsets

object Main {
  def main(args: Array[String]): Unit = {
    val symbols = "ACBDGHKMNSRUTWVYacbdghkmnsrutwvy"
    val complements = "TGVHCDMKNSYAAWBRTGVHCDMKNSYAAWBR"
    val mapping = Array.fill(256)(-1)
    symbols.indices.foreach(i => mapping(symbols.charAt(i).toInt) = complements.charAt(i).toInt)
    val reader = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.ISO_8859_1), 65536)
    val output = new BufferedOutputStream(System.out, 65536)
    val sequence = new java.lang.StringBuilder
    var header: String = null

    def emit(): Unit = {
      if (header != null) {
        output.write(header.getBytes(StandardCharsets.ISO_8859_1))
        output.write(10)
        var i = sequence.length - 1
        var column = 0
        while (i >= 0) {
          val code = sequence.charAt(i).toInt
          val complement = mapping(code)
          require(complement >= 0, s"Invalid IUPAC byte: $code")
          output.write(complement)
          column += 1
          if (column == 60) {
            output.write(10)
            column = 0
          }
          i -= 1
        }
        if (column != 0) output.write(10)
      }
      sequence.setLength(0)
    }

    var line = reader.readLine()
    while (line != null) {
      if (line.startsWith(">")) {
        emit()
        header = line
      } else if (header != null && !line.startsWith(";")) sequence.append(line)
      line = reader.readLine()
    }
    emit()
    output.flush()
  }
}
