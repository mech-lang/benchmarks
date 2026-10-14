/* Scala implementation of the Computer Language Benchmarks Game workload.
 * Java reference: Stefan Krause, Chad Whipkey, Colin D Bennett,
 * The Anh Tran and Enotus. This version explicitly zeroes PBM padding bits.
 * https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
 * See ../LICENSE.benchmarksgame.
 */
import java.io.BufferedOutputStream
import java.nio.charset.StandardCharsets
import java.util.concurrent.{Callable, Executors}
import java.util.concurrent.atomic.AtomicInteger

object Main {
  def main(args: Array[String]): Unit = {
    val n = args(0).toInt
    require(n >= 0)
    val rows = Array.ofDim[Byte](n, (n + 7) / 8)
    val nextRow = new AtomicInteger(0)
    val workers = math.min(8, Runtime.getRuntime.availableProcessors())
    val pool = Executors.newFixedThreadPool(workers)
    try {
      val tasks = (0 until workers).map { _ =>
        pool.submit(new Callable[Unit] {
          def call(): Unit = {
            var y = nextRow.getAndIncrement()
            while (y < n) {
              val imaginary = y * (2.0 / n) - 1.0
              var x = 0
              while (x < n) {
                val real = x * (2.0 / n) - 1.5
                var zr = 0.0
                var zi = 0.0
                var zr2 = 0.0
                var zi2 = 0.0
                var iteration = 0
                while (iteration < 50 && zr2 + zi2 <= 4.0) {
                  zi = 2.0 * zr * zi + imaginary
                  zr = zr2 - zi2 + real
                  zr2 = zr * zr
                  zi2 = zi * zi
                  iteration += 1
                }
                if (zr2 + zi2 <= 4.0) {
                  val byteIndex = x / 8
                  rows(y)(byteIndex) = (rows(y)(byteIndex) | (1 << (7 - x % 8))).toByte
                }
                x += 1
              }
              y = nextRow.getAndIncrement()
            }
          }
        })
      }
      tasks.foreach(_.get())
      val output = new BufferedOutputStream(System.out, 65536)
      output.write(s"P4\n$n $n\n".getBytes(StandardCharsets.US_ASCII))
      rows.foreach(row => output.write(row))
      output.flush()
    } finally pool.shutdown()
  }
}
