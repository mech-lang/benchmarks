std ← •Import "../stdlib/standard.bqn"
# Select the exact THREE record; native FLines handles LF, CRLF and CR.
lines ← •FLines "/dev/stdin"
IsThree ← {(">THREE"≡6↑𝕩)∧(∨´(6⊑7↑𝕩)=" "∾@+9)}
start ← 1+⊑(/IsThree¨lines)∾≠lines
tail ← start↓lines
end ← ⊑(/'>'=⊑¨1↑¨tail)∾≠tail
body ← end↑tail
body /˜↩ (';'≠⊑¨1↑¨body)∧0<≠¨body
dna ← 4|"ACGTacgt"⊐∾body
Pair ← {𝕊 factor‿shift‿left‿right:
 n ← 0⌈(≠right)-shift
 (factor×n↑left)+shift↓right
}
Counts ← {𝕊 width‿wanted‿keys:
 ord ← {
  1<≠𝕩? ⊒ <¨𝕩;
  h ← ⟨⟩ •HashMap ⟨⟩
  {n←0 h.Get 𝕩 ⋄ 𝕩 h.Set n+1 ⋄ n}¨𝕩
 } keys
 width<3? v←0⌈⌈´¨keys⊔1+ord ⋄ v∾((4⋆width)-≠v)⥊0;
 ⟨⌈´ 0∾1+(keys=wanted)/ord⟩
}
Chunk ← {𝕊 start‿rows:
 data ← (rows+17)↑(start↓dna)∾17⥊0
 available ← (≠dna)-start
 p2 ← Pair ⟨4,1,data,data⟩
 p3 ← Pair ⟨4,2,p2,data⟩
 p4 ← Pair ⟨16,2,p2,p2⟩
 p6 ← Pair ⟨64,3,p3,p3⟩
 p12 ← Pair ⟨4096,6,p6,p6⟩
 p18 ← Pair ⟨4096,12,p12,p6⟩
 words ← ⟨data,p2,p3,p4,p6,p12,p18⟩
 widths ← 1‿2‿3‿4‿6‿12‿18
 targets ← 0‿0‿43‿172‿2767‿11337487‿46438350027
 ∾{𝕊 i:
  width ← i⊑widths
  keys ← (rows⌊0⌈available-width+1)↑i⊑words
  Counts ⟨width,i⊑targets,keys⟩
 }¨↕7
}
batchSize ← 100000
jobs ← {⟨𝕩,batchSize⌊(≠dna)-𝕩⟩}¨batchSize×↕⌈(≠dna)÷batchSize
totals ← +´ ⟨25⥊0⟩ ∾ Chunk std._Parallel jobs
Decode ← {"ACGT"⊏˜4|⌊𝕩÷4⋆⌽↕𝕨}
Fixed ← {s←•Repr⌊0.5+1e3×𝕩 ⋄ ¯3(↓∾'.'∾↑) (((4⌈≠s)-(≠s))⥊'0')∾s}
Frequency ← {𝕊 width:
 counts ← {𝕩=1? 4↑totals; 16↑4↓totals} width
 keys ← /0<counts
 ordered ← keys⊏˜⍒keys⊏counts
 {•Out (width Decode 𝕩)∾" "∾Fixed 100×(𝕩⊑counts)÷+´counts}¨ordered
 •Out ""
}
Frequency¨ 1‿2
{𝕊 i: •Out (•Repr (20+i)⊑totals)∾(@+9)∾i⊑⟨"GGT","GGTA","GGTATT","GGTATTTTAATT","GGTATTTTAATTTATAGT"⟩}¨↕5
