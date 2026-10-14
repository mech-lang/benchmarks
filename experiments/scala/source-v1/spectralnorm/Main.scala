/* Scala adaptation of the Computer Language Benchmarks Game program.
 * Contributed by Ziad Hatahet, based on the Go entry by K P anonymous.
 * https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
 * See ../LICENSE.benchmarksgame.
 */
import java.util.Locale
import java.util.concurrent.{Callable, ExecutorService, Executors}

object Main {
  def multiply(input: Array[Double], output: Array[Double], transpose: Boolean,
               pool: ExecutorService, workers: Int): Unit = {
    val n = input.length
    val tasks = (0 until workers).map { worker =>
      pool.submit(new Callable[Unit] {
        def call(): Unit = {
          var i = worker * n / workers
          val end = (worker + 1) * n / workers
          while (i < end) {
            var sum = 0.0
            var j = 0
            while (j < n) {
              val row = if (transpose) j else i
              val column = if (transpose) i else j
              val index = row + column
              val denominator = index * (index + 1) / 2 + row + 1
              sum += input(j) / denominator
              j += 1
            }
            output(i) = sum
            i += 1
          }
        }
      })
    }
    tasks.foreach(_.get())
  }

  def main(args: Array[String]): Unit = {
    val n = args(0).toInt
    require(n > 0)
    val u = Array.fill(n)(1.0)
    val v = new Array[Double](n)
    val temporary = new Array[Double](n)
    val workers = math.min(8, Runtime.getRuntime.availableProcessors())
    val pool = Executors.newFixedThreadPool(workers)
    try {
      var iteration = 0
      while (iteration < 10) {
        multiply(u, temporary, false, pool, workers)
        multiply(temporary, v, true, pool, workers)
        multiply(v, temporary, false, pool, workers)
        multiply(temporary, u, true, pool, workers)
        iteration += 1
      }
      var numerator = 0.0
      var denominator = 0.0
      var i = 0
      while (i < n) {
        numerator += u(i) * v(i)
        denominator += v(i) * v(i)
        i += 1
      }
      System.out.printf(Locale.ROOT, "%.9f\n", Double.box(math.sqrt(numerator / denominator)))
    } finally pool.shutdown()
  }
}
