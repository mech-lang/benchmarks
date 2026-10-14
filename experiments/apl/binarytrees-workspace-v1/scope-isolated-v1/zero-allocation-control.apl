⍝ Scope-isolated diagnostic; Make and Check retain the subject definitions.
⎕IO←0
⎕CT←0
OUT←'w'⎕FIO[3]'/dev/fd/3'
∇ Z←Make D;Left;Right
 →(D>0)/Branch
 Z←0(⊂⍬)(⊂⍬)
 →0
Branch:Left←Make D-1
 Right←Make D-1
 Z←1 Left Right
∇
∇ Z←Check T
 Z←1
 →(0=⊃T[0])/0
 Z←1+(Check ⊃T[1])+Check ⊃T[2]
∇
∇ Initialize
 A←⍬
 B←⍬
 T←⍬
 Counts←7⍴0
 Counts[0]←0
∇
∇ BuildA
 A←⍬
∇
∇ BuildB
 B←⍬
∇
∇ BuildT
 T←⍬
∇
∇ DropT
 T←⍬
∇
∇ DropA
 A←⍬
∇
∇ DropB
 B←⍬
∇
∇ Record I
 Counts[I]←⊃⎕SYL[4;1]
∇
∇ Probe
 Initialize
 Record 0
 BuildA
 Record 1
 BuildB
 Record 2
 BuildT
 Record 3
 DropT
 Record 4
 DropA
 Record 5
 DropB
 Record 6
∇
∇ PrintCounts
 ⊣(('control_deltas=%d,%d,%d,%d,%d,%d',⎕UCS 10)(Counts[1]-Counts[0])(Counts[2]-Counts[0])(Counts[3]-Counts[0])(Counts[4]-Counts[0])(Counts[5]-Counts[0])(Counts[6]-Counts[0]))⎕FIO[22]OUT
∇
∇ Verify;A;B;T
 A←Make 0
 B←Make 0
 T←Make 2
 ⊣(('checks=%d,%d,%d',⎕UCS 10)(Check A)(Check B)(Check T))⎕FIO[22]OUT
∇
Probe
PrintCounts
Verify
⊣⎕FIO[4]OUT
)OFF
