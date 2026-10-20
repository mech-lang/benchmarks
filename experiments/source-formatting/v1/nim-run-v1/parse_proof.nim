# Trusted verification helper; never semantic-check/evaluate/compile input.
import std/[json, os, strutils, sequtils]
import compiler/[parser, lexer, idents, llstream, ast, msgs, options, pathutils]

proc node(n: PNode): JsonNode =
  if n == nil: return newJNull()
  result = %*{"kind": $n.kind}
  case n.kind
  of nkIdent: result["identifier"] = %n.ident.s
  of nkCharLit, nkIntLit..nkUInt64Lit: result["integer"] = %($n.intVal)
  of nkFloatLit..nkFloat128Lit: result["float_bits"] = %($cast[uint64](n.floatVal))
  of nkStrLit, nkRStrLit, nkTripleStrLit: result["string"] = %n.strVal
  of nkSym, nkType: quit("Unexpected semantic AST node", 3)
  else:
    var children = newJArray()
    for i in 0..<n.safeLen: children.add(node(n[i]))
    result["children"] = children

proc proof(filename: string): JsonNode =
  let text = readFile(filename)
  if text.splitLines.anyIt(it.strip.startsWith("#?")):
    quit("Source filter forbidden", 3)
  var conf = newConfigRef()
  var p: Parser
  let file = AbsoluteFile(filename)
  parser.openParser(p, file, llStreamOpen(text), newIdentCache(), conf)
  let tree = parseAll(p)
  closeParser(p)
  var lex: Lexer
  openLexer(lex, file, llStreamOpen(text), newIdentCache(), conf)
  var tok: Token
  var tokens = newJArray()
  var comments = newJArray()
  while true:
    rawGetTok(lex,tok)
    if tok.tokType == tkEof: break
    var value = %*{"kind": $tok.tokType}
    if tok.ident != nil: value["identifier"] = %tok.ident.s
    case tok.tokType
    of tkIntLit..tkUInt64Lit:
      value["integer"] = %($tok.iNumber)
      value["base"] = %($tok.base)
    of tkFloatLit..tkFloat128Lit:
      value["float_bits"] = %($cast[uint64](tok.fNumber))
      value["base"] = %($tok.base)
    of tkStrLit..tkCharLit, tkCustomLit, tkComment: value["literal"] = %tok.literal
    else: discard
    if tok.tokType == tkComment: comments.add(value)
    else: tokens.add(value)
  closeLexer(lex)
  if conf.errorCounter != 0: quit("Native parse/lexer error", 3)
  result = %*{"path": filename, "ast": node(tree), "tokens": tokens,
              "comments": comments, "errors": conf.errorCounter,
              "application_evaluated": false, "macroexpanded": false}

if paramCount() == 0: quit("Explicit source paths required", 3)
var result = newJArray()
for path in commandLineParams(): result.add(proof(absolutePath(path)))
echo $result
