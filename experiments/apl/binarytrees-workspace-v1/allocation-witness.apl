⍝ Diagnostic only. Make and Check are exact retained subject definitions.
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
∇ Probe;A;B;T;Counts
 A←⍬
 B←⍬
 T←⍬
 Counts←7⍴0
 Counts[0]←0
 Counts[0]←⊃⎕SYL[4;1]
 A←Make 0
 Counts[1]←⊃⎕SYL[4;1]
 B←Make 0
 Counts[2]←⊃⎕SYL[4;1]
 T←Make 2
 Counts[3]←⊃⎕SYL[4;1]
 ⊣(('checks=%d,%d,%d',⎕UCS 10)(Check A)(Check B)(Check T))⎕FIO[22]OUT
 T←⍬
 Counts[4]←⊃⎕SYL[4;1]
 A←⍬
 Counts[5]←⊃⎕SYL[4;1]
 B←⍬
 Counts[6]←⊃⎕SYL[4;1]
 ⊣(('live_deltas=%d,%d,%d,%d,%d,%d',⎕UCS 10)(Counts[1]-Counts[0])(Counts[2]-Counts[0])(Counts[3]-Counts[0])(Counts[4]-Counts[0])(Counts[5]-Counts[0])(Counts[6]-Counts[0]))⎕FIO[22]OUT
∇
Probe
⊣⎕FIO[4]OUT
)OFF
