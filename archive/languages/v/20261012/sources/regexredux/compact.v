module main
import os
import regex
const patterns = ['agggtaaa|tttaccct','[cgt]gggtaaa|tttaccc[acg]','a[act]ggtaaa|tttacc[agt]t','ag[act]gtaaa|tttac[agt]ct','agg[act]taaa|ttta[agt]cct','aggg[acg]aaa|ttt[cgt]ccct','agggt[cgt]aa|tt[acg]accct','agggta[cgt]a|t[acg]taccct','agggtaa[cgt]|[acg]ttaccct']
const replacements = ['tHa[Nt]','(aND)|(caN)|(Ha[DS])|(WaS)','(a[NSt])|(BY)','<[^>]*>','[|][^|][^|]*[|]']
const replacement_values = ['<4>','<3>','<2>','|','-']

fn count(sequence string, pattern string) int {
    mut alternatives := []string{}
    for part in pattern.split('|') {
        alternatives << '(${part})'
    }
    mut expression := regex.regex_opt(alternatives.join('|')) or { panic(err) }
    return expression.find_all(sequence).len / 2
}
fn replaced(sequence string) string {
    mut result := sequence
    for i, pattern in replacements {
        mut expression := regex.regex_opt(pattern) or { panic(err) }
        result = expression.replace(result, replacement_values[i])
    }
    return result
}

fn main() {
    input := os.get_raw_stdin().bytestr()
    mut cleanup := regex.regex_opt('(>.*\n)|(\n)') or { panic(err) }
    sequence := cleanup.replace(input, '')
    for pattern in patterns {
        println('${pattern} ${count(sequence, pattern)}')
    }
    final := replaced(sequence)
    println('\n${input.len}\n${sequence.len}\n${final.len}')
}
