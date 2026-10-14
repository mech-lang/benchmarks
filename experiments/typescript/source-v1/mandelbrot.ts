import process = require("node:process");
import { writeSync } from "node:fs";

// Typed source draft; compilation, conformance, work and counts are pending.
/* The Computer Language Benchmarks Game
   https://salsa.debian.org/benchmarksgame-team/benchmarksgame/

   Greg Buchholz's simple C #2 program transliterated by Isaac Gouy.
   TypeScript adaptation uses bounded synchronous output buffering.
*/

function writeAll(bytes: Uint8Array): void {
  let offset = 0;
  while (offset < bytes.length) {
    const written = writeSync(1, bytes, offset, bytes.length - offset);
    if (written === 0) throw new Error("Output made no progress");
    offset += written;
  }
}

const output = new Uint8Array(65536);
let outputLength = 0;
function emitByte(value: number): void {
  output[outputLength++] = value;
  if (outputLength === output.length) {
    writeAll(output);
    outputLength = 0;
  }
}

let bit = 0;
let byte = 0;
const iter = 50, limit = 2.0;
var zr: number, zi: number, cr: number, ci: number, tr: number, ti: number;

const h = process.argv[2] === undefined ? 200 : Number(process.argv[2]), w = h;

writeAll(Buffer.from(`P4\n${w} ${h}\n`, "ascii"));

for (let y = 0; y < h; ++y) {
  for (let x = 0; x < w; ++x) {
    zr = zi = tr = ti = 0;
    cr = 2 * x / w - 1.5;
    ci = 2 * y / h - 1;
    for (let i = 0; i < iter && (tr + ti <= limit * limit); ++i) {
      zi = 2 * zr * zi + ci;
      zr = tr - ti + cr;
      tr = zr * zr;
      ti = zi * zi;
    }

    byte <<= 1;
    if (tr + ti <= limit * limit) byte |= 0x01;
    ++bit;

    if (bit === 8) {
      emitByte(byte);
      byte = 0;
      bit = 0;
    } else if (x === w - 1) {
      byte <<= 8 - w % 8;
      emitByte(byte);
      byte = 0;
      bit = 0;
    }
  }
}

if (outputLength !== 0) writeAll(output.subarray(0, outputLength));
