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
Frame ← {𝕊 width‿frame‿piece‿wanted:
 total ← 0⌈⌊((≠dna)-frame)÷width
 first ← ⌊total×piece÷8
 last ← ⌊total×(piece+1)÷8
 rows ← last-first
 data ← (width×rows)↑(frame+width×first)↓dna
 keys ← {𝕨+4×𝕩}˝⌽⍉rows‿width⥊data
 ord ← {
  1<≠𝕩? ⊒ <¨𝕩;
  h ← ⟨⟩ •HashMap ⟨⟩
  {n←0 h.Get 𝕩 ⋄ 𝕩 h.Set n+1 ⋄ n}¨𝕩
 } keys
 Final ← {⌈´ 0∾1+(keys=𝕩)/ord}
 {𝕊 unused: width<3? {𝕊 unused: v←0⌈⌈´¨keys⊔1+ord ⋄ v∾((4⋆width)-≠v)⥊0} @; Final wanted} @
}
Count ← {𝕊 width‿wanted:
 jobs ← ∾{𝕊 frame: {width‿frame‿𝕩‿wanted}¨↕8}¨↕width
 +´Frame std._Parallel jobs
}
Decode ← {"ACGT"⊏˜4|⌊𝕩÷4⋆⌽↕𝕨}
Fixed ← {s←•Repr⌊0.5+1e3×𝕩 ⋄ ¯3(↓∾'.'∾↑) (((4⌈≠s)-(≠s))⥊'0')∾s}
Frequency ← {𝕊 width:
 counts ← Count width‿0
 keys ← /0<counts
 ordered ← keys⊏˜⍒keys⊏counts
 {•Out (width Decode 𝕩)∾" "∾Fixed 100×(𝕩⊑counts)÷+´counts}¨ordered
 •Out ""
}
Frequency¨ 1‿2
Query ← {𝕊 s:
 key ← +´(4|"ACGTacgt"⊐s)×4⋆⌽↕≠s
 •Out (•Repr Count (≠s)‿key)∾(@+9)∾s
}
Query¨ ⟨"GGT","GGTA","GGTATT","GGTATTTTAATT","GGTATTTTAATTTATAGT"⟩
