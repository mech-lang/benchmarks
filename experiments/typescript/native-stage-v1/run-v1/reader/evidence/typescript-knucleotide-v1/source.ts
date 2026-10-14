// Typed source draft; compilation, conformance, work and counts are pending.
/* The Computer Language Benchmarks Game
   https://salsa.debian.org/benchmarksgame-team/benchmarksgame/

   Naive transliteration from bearophile's program
   contributed by Isaac Gouy
*/

import { createInterface } from "node:readline";

type Frequency = [sequence: string, percentage: number];

async function seq_lines(): Promise<string[]> {
    const stdin = createInterface({
        input: process.stdin,
        crlfDelay: Infinity,
    });
    const lines: string[] = [];
    let started = false;
    for await (const line of stdin) {
        if (line.startsWith(";")) continue;
        if (started) {
            if (line.startsWith(">")) break;
            lines.push(line);
        } else {
            started = line === ">THREE" || line.startsWith(">THREE ") ||
                line.startsWith(">THREE\t");
        }
    }
    return lines;
}

function base_counts(bases: number, seq: string): Map<string, number> {
    const counts = new Map<string, number>();
    const size = seq.length + 1 - bases;
    for (let i = 0; i < size; i++) {
        const nucleo = seq.substring(i,i+bases);
        const v = counts.get(nucleo); if (v !== undefined)
            counts.set(nucleo,v+1);
        else
            counts.set(nucleo,1);
    }
    return counts;
}

function sorted_freq(bases: number, seq: string): Frequency[] {
    const size = seq.length + 1 - bases;
    const counts = base_counts(bases, seq);
    return Array.from(counts)
        .sort((a, b) => b[1] - a[1] ||
            (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0))
        .map((a): Frequency => [a[0], 100.0 * a[1] / size]);
}

function specific_count(code: string, seq: string): number {
    const counts = base_counts(code.length,seq);
    return counts.get(code) ?? 0;
}

function write_freq(a: Frequency): void {
    console.log(`${a[0]} ${a[1].toFixed(3)}`);
}

function main(): void {
    seq_lines().then(a => {
        const seq = a.map((s) => s.toUpperCase()).join("");
        if (/[^ACGT]/.test(seq)) throw new Error("Invalid nucleotide in THREE record");

        for (const base of [1,2]) {
            sorted_freq(base,seq).forEach(write_freq);
            console.log();
        }

        for (const code of ["GGT", "GGTA", "GGTATT",
                "GGTATTTTAATT", "GGTATTTTAATTTATAGT"]) {
            console.log(`${specific_count(code,seq)}\t${code}`);
        }

    } );
}

main()
