// Additive reader from the pinned source-counts-v1 draft; native transport pending.
// Subject files are supplied only as text to a closed virtual filesystem.
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

const schema = "typescript-native-ast-source-v1";
const roles = [
  "statements", "endOfFileToken", "name", "type", "typeParameters", "typeArguments",
  "parameters", "modifiers", "members", "heritageClauses", "declarationList",
  "declarations", "initializer", "expression", "body", "statement", "thenStatement",
  "elseStatement", "condition", "incrementor", "left", "right", "operatorToken",
  "operand", "arguments", "elements", "properties", "propertyName", "types",
  "elementType", "constraint", "default", "questionToken", "exclamationToken",
  "dotDotDotToken", "equalsGreaterThanToken", "asteriskToken", "head",
  "templateSpans", "literal", "tryBlock", "catchClause", "finallyBlock", "block",
  "variableDeclaration", "importClause", "moduleSpecifier", "moduleReference",
  "namedBindings", "attributes", "label", "whenTrue", "whenFalse", "argumentExpression",
];
const maxSourceBytes = 1024 * 1024;
const maxNodes = 100000;
const virtualRoot = "/typescript-source-counts";
const sha = bytes => createHash("sha256").update(bytes).digest("hex");
const json = value => JSON.stringify(value, null, 2) + "\n";
const digestPattern = /^[0-9a-f]{64}$/;
const utf8 = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true });

function pin(file, expected) {
  assert(path.isAbsolute(file) && digestPattern.test(expected), "Invalid file pin");
  const raw = readFileSync(file);
  assert.equal(sha(raw), expected, `Changed pinned file: ${file}`);
  return raw;
}

function writeNew(directory, name, value) {
  const raw = Buffer.from(typeof value === "string" ? value : json(value));
  writeFileSync(path.join(directory, name), raw, { flag: "wx" });
  return sha(raw);
}

function closedFileSystem(files) {
  const directories = new Map([["/", { files: [], directories: [] }]]);
  for (const file of files.keys()) {
    let child = file;
    let isFile = true;
    while (child !== "/") {
      const parent = path.posix.dirname(child);
      if (!directories.has(parent)) directories.set(parent, { files: [], directories: [] });
      const items = directories.get(parent)[isFile ? "files" : "directories"];
      const name = path.posix.basename(child);
      if (!items.includes(name)) items.push(name);
      child = parent;
      isFile = false;
    }
  }
  return {
    readFile: name => files.get(name) ?? null,
    fileExists: name => files.has(name),
    directoryExists: name => directories.has(name),
    getAccessibleEntries: name => directories.get(name) ?? { files: [], directories: [] },
    realpath: name => name,
  };
}

function dumpTree(sourceFile, SyntaxKind, text) {
  assert.equal(sourceFile.text, text, "Compiler AST changed source text");
  const names = new Map();
  for (const [name, value] of Object.entries(SyntaxKind)) {
    if (typeof value !== "number" || /^(First|Last|Count)/.test(name)) continue;
    assert(!names.has(value), `Ambiguous SyntaxKind value: ${name}`);
    names.set(value, name);
  }
  const rows = [];
  const ids = new Map();
  const objects = [];
  function walk(node, parent) {
    assert(rows.length < maxNodes && !ids.has(node), "Oversized or repeated AST node");
    const start = node.getStart(sourceFile);
    const end = node.getEnd();
    const fullStart = node.getFullStart();
    assert(Number.isInteger(start) && Number.isInteger(end) && Number.isInteger(fullStart));
    assert(0 <= fullStart && fullStart <= start && start <= end && end <= text.length);
    assert.equal(node.getText(sourceFile), text.slice(start, end), "AST UTF-16 range differs");
    assert.equal(node.getFullText(sourceFile), text.slice(fullStart, end), "AST full range differs");
    const id = rows.length;
    ids.set(node, id);
    objects.push(node);
    const kind = names.get(node.kind);
    assert(kind, "Unknown native SyntaxKind value");
    const row = { id, parent, kind, native_kind: node.kind, flags: node.flags,
      start_utf16: start, end_utf16: end, full_start_utf16: fullStart,
      text_sha256: sha(Buffer.from(text.slice(start, end), "utf8")), children: [], roles: {} };
    rows.push(row);
    node.forEachChild(child => { row.children.push(walk(child, id)); });
    return id;
  }
  walk(sourceFile, -1);
  assert.equal(rows[0].kind, "SourceFile");
  assert.equal(rows[0].end_utf16, text.length);
  for (let id = 0; id < rows.length; id++) {
    const row = rows[id];
    const node = objects[id];
    for (const role of roles) {
      const value = node[role];
      if (value === undefined) continue;
      if (Array.isArray(value)) {
        const children = value.map(child => {
          assert(ids.has(child) && row.children.includes(ids.get(child)), `Unowned ${role} child`);
          return ids.get(child);
        });
        row.roles[role] = children;
      } else if (value !== null && typeof value === "object" && typeof value.kind === "number") {
        assert(ids.has(value) && row.children.includes(ids.get(value)), `Unowned ${role} child`);
        row.roles[role] = ids.get(value);
      }
    }
    if (typeof node.operator === "number") {
      row.operator_kind = names.get(node.operator);
      assert(row.operator_kind, "Unknown unary operator kind");
    }
    for (const child of row.children) {
      assert(row.full_start_utf16 <= rows[child].full_start_utf16 &&
        rows[child].end_utf16 <= row.end_utf16, "AST child escapes parent");
    }
  }
  return rows;
}

async function main() {
  assert.equal(process.argv.length, 4, "Expected absolute plan path and plan SHA-256");
  const planPath = process.argv[2];
  const planBytes = pin(planPath, process.argv[3]);
  const plan = JSON.parse(utf8.decode(planBytes));
  assert.equal(plan.schema, "typescript-ast-reader-plan-v2");
  assert.equal(plan.typescript.version, "7.0.2", "Reader API version is fixed");
  assert.equal(realpathSync(plan.node.executable), realpathSync(process.execPath));
  assert.equal(plan.node.version, process.version);
  assert.equal(realpathSync(plan.reader.path), realpathSync(fileURLToPath(import.meta.url)));
  pin(plan.reader.path, plan.reader.sha256);
  assert(path.isAbsolute(plan.output) && !existsSync(plan.output), "Fresh absolute output required");
  assert(Array.isArray(plan.inputs) && plan.inputs.length > 0 && plan.inputs.length <= 100);
  const packageRoot = realpathSync(plan.typescript.package_root);
  const metadata = JSON.parse(utf8.decode(pin(path.join(packageRoot, "package.json"),
    plan.typescript.package_json_sha256)));
  assert.equal(metadata.name, "typescript");
  assert.equal(metadata.version, "7.0.2");
  assert.equal(metadata.exports["./unstable/sync"], "./dist/api/sync/api.js");
  assert.equal(metadata.exports["./unstable/ast"], "./dist/ast/index.js");
  assert(path.isAbsolute(plan.typescript.executable), "Pinned compiler executable required");
  const apiPath = path.join(packageRoot, "dist/api/sync/api.js");
  const astPath = path.join(packageRoot, "dist/ast/index.js");
  pin(apiPath, plan.typescript.api_entry_sha256);
  pin(astPath, plan.typescript.ast_entry_sha256);

  const files = new Map();
  const inputs = [];
  const seen = new Set();
  for (const input of plan.inputs) {
    assert(/^[a-z0-9][a-z0-9-]*$/.test(input.id) && !seen.has(input.id), "Invalid input ID");
    seen.add(input.id);
    assert(["application", "fixture"].includes(input.role));
    assert(["ok", "error"].includes(input.expected_parse));
    const bytes = pin(input.source_path, input.sha256);
    assert(bytes.length <= maxSourceBytes);
    const text = utf8.decode(bytes);
    assert(Buffer.from(text, "utf8").equals(bytes), "UTF-8 decoding changed source bytes");
    const virtualPath = `${virtualRoot}/${input.id}.ts`;
    files.set(virtualPath, text);
    inputs.push({ ...input, bytes, text, virtualPath });
  }
  const configPath = `${virtualRoot}/tsconfig.json`;
  const config = { compilerOptions: { target: "ES2022", module: "NodeNext",
    moduleResolution: "NodeNext", noEmit: true, noLib: true, noResolve: true,
    types: [], allowJs: false, strict: true }, files: inputs.map(input => input.virtualPath) };
  files.set(configPath, json(config));
  mkdirSync(plan.output);
  writeFileSync(path.join(plan.output, "plan.json"), planBytes, { flag: "wx" });
  writeNew(plan.output, "parse-config.json", config);
  writeNew(plan.output, "started.json", { schema: "typescript-ast-reader-start-v1",
    pid: process.pid, ppid: process.ppid, node: process.execPath, versions: process.versions,
    typescript_version: metadata.version, api_entry: apiPath, ast_entry: astPath,
    compiler_executable: plan.typescript.executable, plan_sha256: sha(planBytes),
    api_stability: "unstable-version-pinned", native_child_supervision_required: true });

  const { API } = await import(pathToFileURL(apiPath).href);
  const { SyntaxKind } = await import(pathToFileURL(astPath).href);
  assert.equal(typeof API, "function");
  assert.equal(typeof SyntaxKind, "object");
  const api = new API({ tsserverPath: plan.typescript.executable, cwd: plan.output,
    fs: closedFileSystem(files) });
  // The pinned API exposes this child through public JavaScript fields. Its
  // close() sends SIGTERM and unreferences the child; it does not await reaping.
  const child = api.client?.channel?.child;
  assert(child && typeof child.once === "function", "Pinned API child surface changed");
  const childStart = { schema: "typescript-api-child-start-v1", parent_pid: process.pid,
    pid: child.pid ?? null, executable: child.spawnfile, argv: child.spawnargs,
    cwd: process.cwd(), language_cwd: plan.output };
  writeNew(plan.output, "compiler-child-start.json", childStart);
  assert(Number.isInteger(child.pid) && child.pid > 0);
  assert.equal(realpathSync(child.spawnfile), realpathSync(plan.typescript.executable));
  assert.deepEqual(child.spawnargs, [plan.typescript.executable, "--api", "--cwd", plan.output,
    "--callbacks=readFile,fileExists,directoryExists,getAccessibleEntries,realpath"]);
  child.ref();
  const childEvents = [];
  let childError = null;
  // Resolve on error too so an early event cannot become an unhandled rejection.
  const childClosed = new Promise(resolve => {
    child.once("error", error => { childError = String(error?.stack ?? error); });
    child.once("exit", (code, signal) => { childEvents.push({ event: "exit", code, signal }); });
    child.once("close", (code, signal) => {
      childEvents.push({ event: "close", code, signal }); resolve({ code, signal });
    });
  });
  const items = [];
  try {
    const snapshot = api.updateSnapshot({ openProjects: [configPath] });
    assert.equal(snapshot.getProjects().length, 1, "Unexpected compiler project");
    const project = snapshot.getProject(configPath);
    assert(project, "Missing virtual parse-only project");
    assert.deepEqual([...project.rootFiles].sort(), inputs.map(input => input.virtualPath).sort());
    assert.deepEqual([...project.program.getSourceFileNames()].sort(), [...project.rootFiles].sort(),
      "Unexpected source or library loaded");
    for (const input of inputs) {
      const sourceFile = project.program.getSourceFile(input.virtualPath);
      assert(sourceFile && sourceFile.text === input.text, "Missing or changed compiler source");
      const diagnostics = project.program.getSyntacticDiagnostics(input.virtualPath);
      assert(Array.isArray(diagnostics));
      assert.equal(diagnostics.length === 0, input.expected_parse === "ok", "Unexpected parser outcome");
      const nodes = diagnostics.length ? [] : dumpTree(sourceFile, SyntaxKind, input.text);
      const directory = path.join(plan.output, input.id);
      mkdirSync(directory);
      writeFileSync(path.join(directory, "source.ts"), input.bytes, { flag: "wx" });
      const evidence = { schema, id: input.id, source_path: input.source_path,
        source_sha256: input.sha256, source_bytes: input.bytes.length,
        source_utf16_length: input.text.length, source_text: input.text,
        virtual_path: input.virtualPath, offset_units: "UTF-16 code units",
        parser: "TypeScript 7.0.2 native API", native_transport_verified: false,
        parse_diagnostics: diagnostics, nodes, canonical_loc: null, formatted_loc: null,
        chart_admission: false };
      const evidenceSha = writeNew(directory, "ast.json", evidence);
      items.push({ id: input.id, role: input.role, source_sha256: input.sha256,
        ast_sha256: evidenceSha, nodes: nodes.length, parse_diagnostics: diagnostics.length,
        status: diagnostics.length ? "expected-parse-rejection" : "parsed" });
    }
  } finally {
    let closeError = null;
    try { api.close(); } catch (error) { closeError = String(error?.stack ?? error); }
    let timer;
    const closed = await Promise.race([childClosed,
      new Promise(resolve => { timer = setTimeout(() => resolve(null), 5000); })]);
    clearTimeout(timer);
    writeNew(plan.output, "compiler-child-terminal.json", {
      schema: "typescript-api-child-terminal-v1", pid: child.pid, parent_pid: process.pid,
      close_requested: true, close_observed: closed !== null, events: childEvents,
      exit_code: child.exitCode, signal_code: child.signalCode,
      child_error: childError, close_error: closeError,
      cleanup_scope: "API direct child; outer supervisor independently requires an empty process group" });
    assert(closed !== null, "Compiler child close deadline exceeded");
    assert.equal(childError, null); assert.equal(closeError, null);
    assert.deepEqual(childEvents, [{ event: "exit", ...closed }, { event: "close", ...closed }]);
    assert((closed.code === 0 && closed.signal === null) ||
      (closed.code === null && closed.signal === "SIGTERM"), "Unexpected API child shutdown");
    assert.equal(child.exitCode, closed.code); assert.equal(child.signalCode, closed.signal);
  }
  for (const input of inputs) pin(input.source_path, input.sha256);
  pin(planPath, sha(planBytes));
  pin(plan.reader.path, plan.reader.sha256);
  writeNew(plan.output, "report.json", { schema: "typescript-ast-reader-results-v1",
    status: "read-awaiting-transport-and-owner-review", plan_sha256: sha(planBytes), items,
    source_evaluations: 0, subject_main_invocations: 0, emitted_files: 0,
    native_transport_verified: false, canonical_loc: null, formatted_loc: null,
    chart_admission: false });
}

main().catch(error => { process.stderr.write(String(error?.stack ?? error) + "\n"); process.exitCode = 1; });
