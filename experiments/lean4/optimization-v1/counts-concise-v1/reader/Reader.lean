import Lean

open Lean

def span (stx : Syntax) : Json :=
  Json.mkObj [
    ("kind", toJson stx.getKind.toString),
    ("start", toJson (stx.getPos?.map fun p => p.byteIdx)),
    ("end", toJson (stx.getTailPos?.map fun p => p.byteIdx))]

partial def scan (stx : Syntax) : Array Json × Array Json := Id.run do
  let mut tokens := #[]
  let mut statements := #[]
  match stx with
  | .atom .. | .ident .. => tokens := tokens.push (span stx)
  | _ => pure ()
  if stx.getKind == `Lean.Parser.Term.doSeqItem then
    statements := statements.push (span stx)
  for child in stx.getArgs do
    let (ts, ss) := scan child
    tokens := tokens ++ ts
    statements := statements ++ ss
  return (tokens, statements)

def main (files : List String) : IO Unit := do
  unsafe enableInitializersExecution
  let sysroot :: files := files | throw (IO.userError "toolchain path required")
  initSearchPath sysroot
  let env ← importModules (loadExts := true) #[{ module := `Std }] {}
  for file in files do
    let contents ← IO.FS.readFile file
    let parsed ← Parser.testParseModule env file contents
    let (tokens, statements) := scan parsed
    IO.println (Json.mkObj [
      ("source", toJson file),
      ("tokens", toJson tokens),
      ("do_statements", toJson statements)]).compress
