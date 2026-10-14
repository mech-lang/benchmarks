import process = require("node:process");

// Typed source draft; compilation, conformance, work and counts are pending.
/* The Computer Language Benchmarks Game
   https://salsa.debian.org/benchmarksgame-team/benchmarksgame/

   transliterated from Alexander Fyodorov's program by Isaac Gouy
*/

function calculatePi(arg: number): void {
  if (arg === 0) return;
  let i = 0;
  let digits = "";

  let k: bigint = 0n;
  let k1: bigint = 1n;
  let a: bigint = 0n;
  let d: bigint = 1n;
  let m: bigint = 0n;
  let n: bigint = 1n;
  let t: bigint = 0n;
  let u: bigint = 1n;

  while (true) {
    k += 1n;
    k1 += 2n;
    t = n << 1n;
    n *= k;
    a += t;
    a *= k1;
    d *= k1;

    if (a > n) {
      m = n * 3n + a;
      t = m / d;
      u = (m + n) / d;

      if (t === u) {
        digits += t.toString();
        i += 1;

        let last = i >= arg;
        if (i % 10 == 0 || last) {

          console.log(digits.padEnd(10, " ") + '\t:' + i);
          digits = "";
        }

        if (last) break;

        a = (a - d * t) * 10n;
        n = n * 10n;
      }
    }
  }
}


calculatePi(process.argv[2] === undefined ? 30 : Number(process.argv[2]));
