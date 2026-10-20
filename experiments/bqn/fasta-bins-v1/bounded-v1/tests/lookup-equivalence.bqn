# Untimed generic Bins equivalence checks; not imported by production sources.
samples ← (↕139968)÷139968
Check ← {
  cumulative ← +`𝕩
  expected ← +´˘⍉ cumulative ≤⌜ samples
  actual ← cumulative ⍋ samples
  ! expected≡actual
  ! (cumulative⍋⟨⟩)≡⟨⟩
  @
}
Check 0.27‿0.12‿0.12‿0.27∾11⥊0.02
Check 0.3029549426680‿0.1979883004921‿0.1975473066391‿0.3015094502008
thresholds ← 0‿0.5‿0.5‿1
values ← ¯0.25‿0‿0.25‿0.5‿0.75‿1‿1.25
! (thresholds⍋values)≡0‿1‿1‿3‿3‿4‿4
! (thresholds⍋values)≡+´˘⍉thresholds≤⌜values
•Out "PASS: finite FASTA sample domain, threshold equality, duplicates and empty input"
