/* Scala adaptation of the Computer Language Benchmarks Game Java program.
 * Based on Jarkko Miettinen's program; contributed by Tristan Dupont.
 * https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
 * See ../LICENSE.benchmarksgame.
 */
import java.util.concurrent.{Callable, Executors, Future}
import scala.collection.mutable.ArrayBuffer

object Main {
  final class Node(val left: Node, val right: Node) {
    def check(): Int =
      if (left == null) 1 else 1 + left.check() + right.check()
  }

  def tree(depth: Int): Node =
    if (depth == 0) new Node(null, null)
    else new Node(tree(depth - 1), tree(depth - 1))

  def main(args: Array[String]): Unit = {
    val maxDepth = math.max(6, args(0).toInt)
    val stretchDepth = maxDepth + 1
    println(s"stretch tree of depth $stretchDepth\t check: ${tree(stretchDepth).check()}")
    val longLived = tree(maxDepth)
    val workers = math.min(8, Runtime.getRuntime.availableProcessors())
    val pool = Executors.newFixedThreadPool(workers)
    val results = ArrayBuffer.empty[Future[String]]
    try {
      var depth = 4
      while (depth <= maxDepth) {
        val d = depth
        results += pool.submit(new Callable[String] {
          def call(): String = {
            val iterations = 1 << (maxDepth - d + 4)
            var check = 0
            var i = 0
            while (i < iterations) {
              check += tree(d).check()
              i += 1
            }
            s"$iterations\t trees of depth $d\t check: $check"
          }
        })
        depth += 2
      }
      results.foreach(result => println(result.get()))
      println(s"long lived tree of depth $maxDepth\t check: ${longLived.check()}")
    } finally pool.shutdown()
  }
}
