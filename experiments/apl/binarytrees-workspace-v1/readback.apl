⍝ Diagnostic only; used both before and after setup.apl in one process.
OUT←'a'⎕FIO[3]'/dev/fd/3'
⊣(('wa_scale=%d',⎕UCS 10)(⊃⎕SYL[(⎕IO+31);(⎕IO+1)]))⎕FIO[22]OUT
⊣⎕FIO[4]OUT
