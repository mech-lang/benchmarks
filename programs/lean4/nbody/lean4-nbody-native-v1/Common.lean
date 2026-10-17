import Std

namespace Bench

@[extern "lean_bench_fixed"]
opaque fixed (value : Float) (digits : UInt32) : String

def argument (args : List String) : IO Nat :=
  match args with
  | [value] =>
    match value.toNat? with
    | some n => pure n
    | none => throw (IO.userError "expected one nonnegative integer")
  | _ => throw (IO.userError "expected one nonnegative integer")

def readAll : IO ByteArray := do
  (← IO.getStdin).readBinToEnd

def writeBytes (bytes : ByteArray) : IO Unit := do
  (← IO.getStdout).write bytes

def finish : IO Unit := do
  (← IO.getStdout).flush

end Bench
