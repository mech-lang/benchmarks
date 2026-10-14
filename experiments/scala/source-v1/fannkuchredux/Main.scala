/* Scala adaptation of the Computer Language Benchmarks Game program.
 * Contributed by Oleg Mazurov, June 2010.
 * https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
 * See ../LICENSE.benchmarksgame.
 */
import java.util.concurrent.{Callable, Executors}
import java.util.concurrent.atomic.AtomicInteger

object Main {
  final class Worker(n: Int, factorial: Array[Int], chunkSize: Int, taskCount: Int,
                     nextTask: AtomicInteger, maxima: Array[Int], checksums: Array[Int])
      extends Callable[Unit] {
    private val permutation = new Array[Int](n)
    private val temporary = new Array[Int](n)
    private val count = new Array[Int](n)

    def firstPermutation(index: Int): Unit = {
      var i = 0
      while (i < n) {
        permutation(i) = i
        i += 1
      }
      var remaining = index
      i = n - 1
      while (i > 0) {
        val digit = remaining / factorial(i)
        count(i) = digit
        remaining %= factorial(i)
        System.arraycopy(permutation, 0, temporary, 0, i + 1)
        var j = 0
        while (j <= i) {
          val shifted = j + digit
          permutation(j) = temporary(if (shifted <= i) shifted else shifted - i - 1)
          j += 1
        }
        i -= 1
      }
    }

    def nextPermutation(): Unit = {
      var first = permutation(1)
      permutation(1) = permutation(0)
      permutation(0) = first
      var i = 1
      count(i) += 1
      while (count(i) > i) {
        count(i) = 0
        i += 1
        val next = permutation(1)
        permutation(0) = next
        var j = 1
        while (j < i) {
          permutation(j) = permutation(j + 1)
          j += 1
        }
        permutation(i) = first
        first = next
        count(i) += 1
      }
    }

    def flips(): Int = {
      System.arraycopy(permutation, 0, temporary, 0, n)
      var result = 0
      while (temporary(0) != 0) {
        var left = 0
        var right = temporary(0)
        while (left < right) {
          val value = temporary(left)
          temporary(left) = temporary(right)
          temporary(right) = value
          left += 1
          right -= 1
        }
        result += 1
      }
      result
    }

    def call(): Unit = {
      var task = nextTask.getAndIncrement()
      while (task < taskCount) {
        var index = task * chunkSize
        val end = math.min(factorial(n), index + chunkSize)
        firstPermutation(index)
        var maximum = 0
        var checksum = 0
        while (index < end) {
          if (permutation(0) != 0) {
            val value = flips()
            maximum = math.max(maximum, value)
            checksum += (if (index % 2 == 0) value else -value)
          }
          index += 1
          if (index < end) nextPermutation()
        }
        maxima(task) = maximum
        checksums(task) = checksum
        task = nextTask.getAndIncrement()
      }
    }
  }

  def main(args: Array[String]): Unit = {
    val n = args(0).toInt
    require(n >= 0 && n <= 12)
    if (n <= 1) {
      println(s"0\nPfannkuchen($n) = 0")
      return
    }
    val factorial = new Array[Int](n + 1)
    factorial(0) = 1
    var i = 1
    while (i <= n) {
      factorial(i) = factorial(i - 1) * i
      i += 1
    }
    val chunkSize = (factorial(n) + 149) / 150
    val taskCount = (factorial(n) + chunkSize - 1) / chunkSize
    val maxima = new Array[Int](taskCount)
    val checksums = new Array[Int](taskCount)
    val nextTask = new AtomicInteger(0)
    val workers = math.min(8, Runtime.getRuntime.availableProcessors())
    val pool = Executors.newFixedThreadPool(workers)
    try {
      val tasks = (0 until workers).map { _ =>
        pool.submit(new Worker(n, factorial, chunkSize, taskCount, nextTask, maxima, checksums))
      }
      tasks.foreach(_.get())
      println(s"${checksums.sum}\nPfannkuchen($n) = ${maxima.max}")
    } finally pool.shutdown()
  }
}
