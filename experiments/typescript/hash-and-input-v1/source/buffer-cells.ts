/* The Computer Language Benchmarks Game
   https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
   Derived from the retained TypeScript transliteration of bearophile's
   program contributed by Isaac Gouy. Rolling numeric-key adaptation.
*/
import { readFileSync } from "node:fs";

function sequence(): Uint8Array {
    const raw = readFileSync(0);
    let start = -1;
    let end = raw.length;
    let length = 0;
    let offset = 0;
    while (offset < raw.length) {
        const first = offset;
        while (offset < raw.length && raw[offset] !== 10 && raw[offset] !== 13) offset++;
        const last = offset;
        if (offset < raw.length && raw[offset] === 13) offset++;
        if (offset < raw.length && raw[offset] === 10) offset++;
        if (first === last) continue;
        if (raw[first] === 62) {
            if (start >= 0) { end = first; break; }
            if (last - first >= 6 && raw[first + 1] === 84 && raw[first + 2] === 72 &&
                raw[first + 3] === 82 && raw[first + 4] === 69 && raw[first + 5] === 69 &&
                (last - first === 6 || raw[first + 6] === 32 || raw[first + 6] === 9)) start = offset;
        } else if (start >= 0 && raw[first] !== 59) {
            length += last - first;
        }
    }
    const bases = new Uint8Array(length);
    let output = 0;
    let lineStart = true;
    for (let i = start < 0 ? end : start; i < end; i++) {
        const byte = raw[i];
        if (byte === 10 || byte === 13) { lineStart = true; continue; }
        if (lineStart && byte === 59) {
            while (i < end && raw[i] !== 10 && raw[i] !== 13) i++;
            lineStart = true;
            continue;
        }
        lineStart = false;
        switch (byte) {
            case 65: case 97: bases[output++] = 0; break;
            case 67: case 99: bases[output++] = 1; break;
            case 71: case 103: bases[output++] = 2; break;
            case 84: case 116: bases[output++] = 3; break;
            default: throw new Error("Invalid nucleotide in THREE record");
        }
    }
    return bases;
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
