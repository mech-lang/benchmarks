// SPDX-License-Identifier: Apache-2.0 AND BSD-3-Clause
// Alternative to the local PCRE2 adaptation of regex-redux C# #2.
// Original: Michael Ganss, derived from Josh Goldfoot; Anthony Lloyd.
// https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/regexredux-csharpcore-2.html
using System;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

static partial class Program
{
    static void Main()
    {
        using var input = new MemoryStream();
        Console.OpenStandardInput().CopyTo(input);
        string raw = Encoding.Latin1.GetString(input.GetBuffer(), 0, checked((int)input.Length));
        string sequence = Clean().Replace(raw, "");
        Regex[] patterns = [P0(), P1(), P2(), P3(), P4(), P5(), P6(), P7(), P8()];
        int[] counts = new int[patterns.Length];
        string changed = sequence;
        Parallel.For(0, patterns.Length + 1, new ParallelOptions { MaxDegreeOfParallelism = 8 }, job =>
        {
            if (job < patterns.Length) counts[job] = patterns[job].Count(sequence);
            else
            {
                (Regex Pattern, string Replacement)[] replacements = [
                    (S0(), "<4>"), (S1(), "<3>"), (S2(), "<2>"), (S3(), "|"), (S4(), "-")];
                foreach (var (pattern, replacement) in replacements)
                    changed = pattern.Replace(changed, replacement);
            }
        });
        for (int i = 0; i < patterns.Length; i++) Console.WriteLine($"{patterns[i]} {counts[i]}");
        Console.WriteLine($"\n{raw.Length}\n{sequence.Length}\n{changed.Length}");
    }

    [GeneratedRegex(">[^\n]*\n|\n", RegexOptions.CultureInvariant)]
    private static partial Regex Clean();
    [GeneratedRegex("agggtaaa|tttaccct", RegexOptions.CultureInvariant)]
    private static partial Regex P0();
    [GeneratedRegex("[cgt]gggtaaa|tttaccc[acg]", RegexOptions.CultureInvariant)]
    private static partial Regex P1();
    [GeneratedRegex("a[act]ggtaaa|tttacc[agt]t", RegexOptions.CultureInvariant)]
    private static partial Regex P2();
    [GeneratedRegex("ag[act]gtaaa|tttac[agt]ct", RegexOptions.CultureInvariant)]
    private static partial Regex P3();
    [GeneratedRegex("agg[act]taaa|ttta[agt]cct", RegexOptions.CultureInvariant)]
    private static partial Regex P4();
    [GeneratedRegex("aggg[acg]aaa|ttt[cgt]ccct", RegexOptions.CultureInvariant)]
    private static partial Regex P5();
    [GeneratedRegex("agggt[cgt]aa|tt[acg]accct", RegexOptions.CultureInvariant)]
    private static partial Regex P6();
    [GeneratedRegex("agggta[cgt]a|t[acg]taccct", RegexOptions.CultureInvariant)]
    private static partial Regex P7();
    [GeneratedRegex("agggtaa[cgt]|[acg]ttaccct", RegexOptions.CultureInvariant)]
    private static partial Regex P8();
    [GeneratedRegex("tHa[Nt]", RegexOptions.CultureInvariant)]
    private static partial Regex S0();
    [GeneratedRegex("aND|caN|Ha[DS]|WaS", RegexOptions.CultureInvariant)]
    private static partial Regex S1();
    [GeneratedRegex("a[NSt]|BY", RegexOptions.CultureInvariant)]
    private static partial Regex S2();
    [GeneratedRegex("<[^>]*>", RegexOptions.CultureInvariant)]
    private static partial Regex S3();
    [GeneratedRegex("\\|[^|][^|]*\\|", RegexOptions.CultureInvariant)]
    private static partial Regex S4();
}
