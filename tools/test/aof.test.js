"use strict";
/** Tests for the aof Node package: validation, path expansion, and CLI. */

const { test } = require("node:test");
const assert = require("node:assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");

const {
  loadSchema,
  validateFile,
  semanticChecks,
  expandPaths,
} = require("../lib/validator");

const TOOLS_DIR = path.resolve(__dirname, "..");
const REPO_ROOT = path.resolve(TOOLS_DIR, "..");
const EXAMPLES_DIR = path.join(REPO_ROOT, "examples");
const EXAMPLE_FILES = fs
  .readdirSync(EXAMPLES_DIR)
  .filter((f) => f.endsWith(".yaml"))
  .map((f) => path.join(EXAMPLES_DIR, f))
  .sort();
const BIN = path.join(TOOLS_DIR, "bin", "aof.js");

test("example contracts are discovered", () => {
  assert.ok(EXAMPLE_FILES.length > 0);
});

test("every example contract validates", () => {
  const schema = loadSchema();
  for (const f of EXAMPLE_FILES) {
    const { passed, errors } = validateFile(f, schema);
    assert.ok(passed, `${path.basename(f)} failed: ${JSON.stringify(errors)}`);
  }
});

test("an invalid contract fails", () => {
  const schema = loadSchema();
  const tmp = path.join(os.tmpdir(), `aof-bad-${Date.now()}.yaml`);
  fs.writeFileSync(tmp, "apiVersion: aof/v1\nkind: AgentOwnershipContract\n");
  try {
    const { passed, errors } = validateFile(tmp, schema);
    assert.equal(passed, false);
    assert.ok(errors.length > 0);
  } finally {
    fs.unlinkSync(tmp);
  }
});

test("semantic checks catch bad SLA values", () => {
  const errors = semanticChecks({ sla: { availability: 150, max_latency_ms: 0 } });
  assert.ok(errors.some((e) => e.includes("availability")));
  assert.ok(errors.some((e) => e.includes("max_latency_ms")));
});

test("semantic checks catch non-sequential escalation levels", () => {
  const errors = semanticChecks({
    ownership: { escalation_path: [{ level: 1 }, { level: 3 }] },
  });
  assert.ok(errors.some((e) => e.includes("sequential")));
});

test("expandPaths resolves a directory to its yaml files", () => {
  const files = expandPaths([EXAMPLES_DIR]);
  assert.equal(files.length, EXAMPLE_FILES.length);
});

test("bundled schema matches canonical schema/v1", () => {
  const canonical = fs.readFileSync(
    path.join(REPO_ROOT, "schema", "v1", "agent-ownership-contract.schema.json")
  );
  const bundled = fs.readFileSync(
    path.join(TOOLS_DIR, "aof", "schema", "agent-ownership-contract.schema.json")
  );
  assert.ok(canonical.equals(bundled), "bundled schema drifted from schema/v1/");
});

test("CLI: aof validate on a directory exits 0", () => {
  execFileSync("node", [BIN, "validate", EXAMPLES_DIR], { stdio: "pipe" });
});

test("CLI: aof validate --strict on an empty dir exits 1", () => {
  const empty = fs.mkdtempSync(path.join(os.tmpdir(), "aof-empty-"));
  assert.throws(() =>
    execFileSync("node", [BIN, "validate", "--strict", empty], { stdio: "pipe" })
  );
  // non-strict succeeds (warning only)
  execFileSync("node", [BIN, "validate", empty], { stdio: "pipe" });
});

test("CLI: aof validate --output json emits parseable JSON", () => {
  const out = execFileSync(
    "node",
    [BIN, "validate", "--output", "json", EXAMPLE_FILES[0]],
    { encoding: "utf-8" }
  );
  const payload = JSON.parse(out);
  assert.equal(payload.total, 1);
  assert.equal(payload.passed, 1);
});

test("CLI: aof export stub exits 2", () => {
  // execFileSync throws on non-zero exit; capture the status code.
  let code = 0;
  try {
    execFileSync("node", [BIN, "export"], { stdio: "pipe" });
  } catch (e) {
    code = e.status;
  }
  assert.equal(code, 2);
});
