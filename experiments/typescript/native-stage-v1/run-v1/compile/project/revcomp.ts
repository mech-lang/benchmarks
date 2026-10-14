// TypeScript reverse-complement source draft; native qualification is pending.
// The Computer Language Benchmarks Game workload:
// https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
// Existing Node.js comparison: Joe Farro, with parts by Jos Hirth and 10iii.
// This record parser and output traversal are newly authored for this bundle.
import { readFileSync, writeSync } from "node:fs";
import process = require("node:process");

const symbols = "ACBDGHKMNSRUTWVYacbdghkmnsrutwvy";
const complements = "TGVHCDMKNSYAAWBRTGVHCDMKNSYAAWBR";
const complement = new Uint8Array(256);
for (let index = 0; index < symbols.length; index++) {
    complement[symbols.charCodeAt(index)] = complements.charCodeAt(index);
}

function writeAll(fd: number, bytes: Uint8Array): void {
    let offset = 0;
    while (offset < bytes.length) {
        const written = writeSync(fd, bytes, offset, bytes.length - offset);
        if (written === 0) throw new Error("Output made no progress");
        offset += written;
    }
}

function main(): void {
    const input = readFileSync(0);
    const sequence = Buffer.allocUnsafe(input.length);
    const output = Buffer.allocUnsafe(61 * 1024);
    const newline = Buffer.from([10]);
    let header: Buffer | null = null;
    let sequenceLength = 0;

    function emitRecord(): void {
        if (header === null) return;
        writeAll(1, header);
        writeAll(1, newline);
        let position = 0;
        let column = 0;
        for (let index = sequenceLength - 1; index >= 0; index--) {
            const original = sequence[index];
            const mapped = complement[original];
            if (mapped === 0) {
                throw new Error(`Invalid IUPAC byte: ${original}`);
            }
            output[position++] = mapped;
            column++;
            if (column === 60) {
                output[position++] = 10;
                column = 0;
            }
            if (position === output.length) {
                writeAll(1, output);
                position = 0;
            }
        }
        if (column !== 0) output[position++] = 10;
        if (position !== 0) writeAll(1, output.subarray(0, position));
    }

    let lineStart = 0;
    for (let index = 0; index <= input.length; index++) {
        if (index !== input.length && input[index] !== 10 && input[index] !== 13) {
            continue;
        }
        if (lineStart < index) {
            const first = input[lineStart];
            if (first === 62) {
                emitRecord();
                header = input.subarray(lineStart, index);
                sequenceLength = 0;
            } else if (header !== null && first !== 59) {
                sequenceLength += input.copy(sequence, sequenceLength, lineStart, index);
            }
        }
        lineStart = index + 1;
    }
    emitRecord();
}

try {
    main();
} catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    writeAll(2, Buffer.from(message + "\n", "utf8"));
    process.exitCode = 1;
}
