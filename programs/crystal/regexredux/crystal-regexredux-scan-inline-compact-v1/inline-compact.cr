PATTERNS = [
  /agggtaaa|tttaccct/,
  /[cgt]gggtaaa|tttaccc[acg]/,
  /a[act]ggtaaa|tttacc[agt]t/,
  /ag[act]gtaaa|tttac[agt]ct/,
  /agg[act]taaa|ttta[agt]cct/,
  /aggg[acg]aaa|ttt[cgt]ccct/,
  /agggt[cgt]aa|tt[acg]accct/,
  /agggta[cgt]a|t[acg]taccct/,
  /agggtaa[cgt]|[acg]ttaccct/,
]
SUBSTITUTIONS = [
  {/tHa[Nt]/, "<4>"},
  {/aND|caN|Ha[DS]|WaS/, "<3>"},
  {/a[NSt]|BY/, "<2>"},
  {/<[^>]*>/, "|"},
  {/\|[^|][^|]*\|/, "-"},
]
input = STDIN.gets_to_end
original_length = input.bytesize
sequence = input.gsub(/>[^\n]*\n|\n/, "")
cleaned_length = sequence.bytesize

PATTERNS.each { |pattern| puts "#{pattern.source} #{sequence.scan(pattern).size}" }

SUBSTITUTIONS.each { |pair| sequence = sequence.gsub(pair[0], pair[1]) }
puts ""
puts original_length
puts cleaned_length
puts sequence.bytesize
