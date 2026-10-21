// SPDX-License-Identifier: Apache-2.0 AND BSD-3-Clause
// Alternative to the local PCRE2 adaptation of regex-redux C# #2.
// Original: Michael Ganss, derived from Josh Goldfoot; Anthony Lloyd.
// https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/regexredux-csharpcore-2.html
using System;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

static class Program
{
    static void Main()
    {
        using var input = new MemoryStream();
        Console.OpenStandardInput().CopyTo(input);
        string raw = Encoding.Latin1.GetString(input.GetBuffer(), 0, checked((int)input.Length));
        const RegexOptions options = RegexOptions.CultureInvariant;
        string sequence = Regex.Replace(raw, ">[^\n]*\n|\n", "", options);
        string[] patterns = [
            "agggtaaa|tttaccct", "[cgt]gggtaaa|tttaccc[acg]", "a[act]ggtaaa|tttacc[agt]t",
            "ag[act]gtaaa|tttac[agt]ct", "agg[act]taaa|ttta[agt]cct", "aggg[acg]aaa|ttt[cgt]ccct",
            "agggt[cgt]aa|tt[acg]accct", "agggta[cgt]a|t[acg]taccct", "agggtaa[cgt]|[acg]ttaccct"];
        foreach (string pattern in patterns)
            Console.WriteLine($"{pattern} {Regex.Count(sequence, pattern, options)}");
        (string Pattern, string Replacement)[] replacements = [
            ("tHa[Nt]", "<4>"), ("aND|caN|Ha[DS]|WaS", "<3>"), ("a[NSt]|BY", "<2>"),
            ("<[^>]*>", "|"), ("\\|[^|][^|]*\\|", "-")];
        string changed = sequence;
        foreach (var (pattern, replacement) in replacements)
            changed = Regex.Replace(changed, pattern, replacement, options);
        Console.WriteLine($"\n{raw.Length}\n{sequence.Length}\n{changed.Length}");
    }
}
