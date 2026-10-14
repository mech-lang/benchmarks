// Typed source draft; compilation, conformance, work and counts are pending.
/* The Computer Language Benchmarks Game
   https://salsa.debian.org/benchmarksgame-team/benchmarksgame/

   regex-dna program contributed by Jesse Millikan
   Base on the Ruby version by jose fco. gonzalez
   fixed by Matthew Wilson
   ported to Node.js and sped up by Roman Pletnev
   converted from regex-dna program
   fixed by Josh Goldfoot
   multi thread by Andrey Filatkin
   sequential by Isaac Gouy
*/

import { readFileSync } from 'node:fs';

function mainThread(): void {
    const regExps: RegExp[] = [
        /agggtaaa|tttaccct/g,
        /[cgt]gggtaaa|tttaccc[acg]/g,
        /a[act]ggtaaa|tttacc[agt]t/g,
        /ag[act]gtaaa|tttac[agt]ct/g,
        /agg[act]taaa|ttta[agt]cct/g,
        /aggg[acg]aaa|ttt[cgt]ccct/g,
        /agggt[cgt]aa|tt[acg]accct/g,
        /agggta[cgt]a|t[acg]taccct/g,
        /agggtaa[cgt]|[acg]ttaccct/g
    ];

    let data = readFileSync(0, 'latin1');
    const initialLen = data.length;

    data = data.replace(/>[^\n]*\n|\n/g, '');
    const cleanedLen = data.length;

    for (let j = 0; j < regExps.length; j++) {
        const re = regExps[j];
        const m = data.match(re);
        console.log(re.source, m ? m.length : 0);
    }

    const endLen = data
        .replace(/tHa[Nt]/g, '<4>')
        .replace(/aND|caN|Ha[DS]|WaS/g, '<3>')
        .replace(/a[NSt]|BY/g, '<2>')
        .replace(/<[^>]*>/g, '|')
        .replace(/\|[^|][^|]*\|/g, '-')
        .length;

    console.log(`\n${initialLen}\n${cleanedLen}\n${endLen}`);
}

mainThread();
