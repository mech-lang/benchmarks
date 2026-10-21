/* The Computer Language Benchmarks Game
   https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
   Derived from the retained TypeScript transliteration of bearophile's
   program contributed by Isaac Gouy. Rolling numeric-key adaptation.
*/
import { createInterface } from "node:readline";

async function sequence(): Promise<Uint8Array> {
    const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
    const lines: string[] = [];
    let started = false;
    for await (const line of input) {
        if (line.startsWith(";")) continue;
        if (started) {
            if (line.startsWith(">")) break;
            lines.push(line);
        } else {
            started = line === ">THREE" || line.startsWith(">THREE ") || line.startsWith(">THREE\t");
        }
    }
    return encode(lines.join("").toUpperCase());
}

function encode(text: string): Uint8Array {
    const result = new Uint8Array(text.length);
    for (let i = 0; i < text.length; i++) {
        switch (text.charCodeAt(i)) {
            case 65: result[i] = 0; break;
            case 67: result[i] = 1; break;
            case 71: result[i] = 2; break;
            case 84: result[i] = 3; break;
            default: throw new Error("Invalid nucleotide in THREE record");
        }
    }
    return result;
}

type CountCell = { value: number };

function counts(width: number, bases: Uint8Array): Map<number, CountCell> {
    const table = new Map<number, CountCell>();
    const modulus = 4 ** width;
    let key = 0;
    for (let i = 0; i < bases.length; i++) {
        key = (key * 4 + bases[i]) % modulus;
        if (i + 1 >= width) {
            const cell = table.get(key);
            if (cell === undefined) table.set(key, { value: 1 });
            else cell.value++;
        }
    }
    return table;
}

function decode(key: number, width: number): string {
    let text = "";
    for (let i = 0; i < width; i++) {
        text = "ACGT"[key % 4] + text;
        key = Math.floor(key / 4);
    }
    return text;
}

async function main(): Promise<void> {
    const bases = await sequence();
    for (const width of [1, 2]) {
        const entries = Array.from(counts(width, bases), ([key, cell]) => [key, cell.value] as const).sort((a, b) => b[1] - a[1] || a[0] - b[0]);
        for (const [key, count] of entries) {
            console.log(`${decode(key, width)} ${(100 * count / (bases.length - width + 1)).toFixed(3)}`);
        }
        console.log();
    }
    for (const query of ["GGT", "GGTA", "GGTATT", "GGTATTTTAATT", "GGTATTTTAATTTATAGT"]) {
        let key = 0;
        for (const base of encode(query)) key = key * 4 + base;
        const table = counts(query.length, bases);
        console.log(`${table.get(key)?.value ?? 0}\t${query}`);
    }
}

main();
