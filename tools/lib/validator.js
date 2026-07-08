"use strict";
/**
 * Core validation logic for the Agent Ownership Framework (AOF).
 *
 * Single source of truth shared by the `aof` CLI (bin/aof.js) and the
 * deprecated standalone validate-contract.js shim.
 *
 * @license MIT
 */

const fs = require("fs");
const path = require("path");

let yaml, Ajv, addFormats;

try {
  yaml = require("js-yaml");
} catch {
  console.error("ERROR: js-yaml is required. Run: npm install in the tools/ directory.");
  process.exit(1);
}

try {
  const AjvModule = require("ajv");
  Ajv = AjvModule.default || AjvModule;
} catch {
  console.error("ERROR: ajv is required. Run: npm install in the tools/ directory.");
  process.exit(1);
}

try {
  const AjvFormatsModule = require("ajv-formats");
  addFormats = AjvFormatsModule.default || AjvFormatsModule;
} catch {
  console.error("ERROR: ajv-formats is required. Run: npm install in the tools/ directory.");
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Schema loading — canonical repo copy first, bundled package copy as fallback.
// ---------------------------------------------------------------------------

/** @returns {string[]} ordered candidate paths for the JSON Schema */
function schemaCandidatePaths() {
  const paths = [];
  if (process.env.AOF_SCHEMA_PATH) paths.push(process.env.AOF_SCHEMA_PATH);
  // Repo layout: tools/lib/../../schema/v1/...
  paths.push(
    path.resolve(__dirname, "..", "..", "schema", "v1", "agent-ownership-contract.schema.json")
  );
  // Bundled package copy: tools/aof/schema/... (kept identical to canonical by CI).
  paths.push(
    path.resolve(__dirname, "..", "aof", "schema", "agent-ownership-contract.schema.json")
  );
  return paths;
}

/** @returns {object} parsed JSON Schema */
function loadSchema() {
  for (const p of schemaCandidatePaths()) {
    if (p && fs.existsSync(p)) {
      return JSON.parse(fs.readFileSync(p, "utf-8"));
    }
  }
  throw new Error(
    "AOF JSON Schema not found. Looked in:\n  " +
      schemaCandidatePaths().join("\n  ") +
      "\nSet AOF_SCHEMA_PATH to point at agent-ownership-contract.schema.json."
  );
}

// ---------------------------------------------------------------------------
// Semantic checks
// ---------------------------------------------------------------------------

const EMAIL_RE = /^[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+$/;

function checkEmail(value, fieldPath) {
  if (!EMAIL_RE.test(value)) {
    return `${fieldPath}: '${value}' is not a valid email address`;
  }
  return null;
}

/**
 * @param {object} contract
 * @returns {string[]} error messages (empty means all checks passed)
 */
function semanticChecks(contract) {
  const errors = [];

  const sla = contract.sla || {};
  if (typeof sla === "object") {
    const availability = sla.availability;
    if (availability !== undefined) {
      if (typeof availability !== "number") {
        errors.push("sla.availability: must be a number (e.g., 99.9), not a string");
      } else if (availability < 0 || availability > 100) {
        errors.push(`sla.availability: ${availability} is out of range — must be 0 to 100`);
      }
    }
    const maxLatency = sla.max_latency_ms;
    if (maxLatency !== undefined) {
      if (!Number.isInteger(maxLatency)) {
        errors.push("sla.max_latency_ms: must be an integer");
      } else if (maxLatency < 1) {
        errors.push(`sla.max_latency_ms: ${maxLatency} must be >= 1`);
      }
    }
  }

  const ownership = contract.ownership || {};
  const escalation = ownership.escalation_path || [];
  if (Array.isArray(escalation) && escalation.length > 0) {
    const levels = [];
    escalation.forEach((entry, i) => {
      if (entry && typeof entry === "object") {
        if (entry.level !== undefined) levels.push(entry.level);
        if (entry.email && typeof entry.email === "string") {
          const err = checkEmail(entry.email, `ownership.escalation_path[${i}].email`);
          if (err) errors.push(err);
        }
      }
    });
    if (levels.length > 0) {
      const sorted = [...levels].sort((a, b) => a - b);
      const expected = Array.from({ length: levels.length }, (_, i) => i + 1);
      if (JSON.stringify(sorted) !== JSON.stringify(expected)) {
        errors.push(
          `ownership.escalation_path: levels ${JSON.stringify(sorted)} are not sequential ` +
            `starting at 1 — expected ${JSON.stringify(expected)}`
        );
      }
    }
  }

  const risk = contract.risk || {};
  if (typeof risk === "object" && risk.kill_switch_owner && typeof risk.kill_switch_owner === "string") {
    const err = checkEmail(risk.kill_switch_owner, "risk.kill_switch_owner");
    if (err) errors.push(err);
  }

  return errors;
}

// ---------------------------------------------------------------------------
// schema_version (v2, additive) and lifecycle enforcement
// ---------------------------------------------------------------------------

const DEFAULT_SCHEMA_VERSION = "1.0";

/** @returns {string} declared schema_version or the 1.0 default */
function schemaVersionOf(contract) {
  const v = contract && contract.schema_version;
  return typeof v === "string" && v ? v : DEFAULT_SCHEMA_VERSION;
}

/** @returns {string|null} informational notice for contracts without schema_version */
function schemaVersionNotice(contract) {
  if (!(contract && contract.schema_version)) {
    return (
      `schema_version not declared — assuming ${DEFAULT_SCHEMA_VERSION} (v1). ` +
      "All v2 fields are optional; this contract is valid."
    );
  }
  return null;
}

/** Parse a YYYY-MM-DD string to a UTC-midnight Date, or null. */
function parseIsoDate(value) {
  if (typeof value !== "string") return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());
  if (!m) return null;
  const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
  return Number.isNaN(d.getTime()) ? null : d;
}

/**
 * Flag contracts whose lifecycle/governance dates have passed. Returns warning
 * strings. Warnings never fail validation on their own; `--strict` promotes
 * them to failures. Only explicit date fields are evaluated.
 * @returns {string[]}
 */
function lifecycleChecks(contract, today) {
  const now = today || new Date();
  const todayMid = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  const warnings = [];
  const lifecycle = (contract && contract.lifecycle) || {};
  const status = lifecycle.status;

  const overdue = (value, label, msg) => {
    const d = parseIsoDate(value);
    if (d && d < todayMid) warnings.push(`${label} ${value} ${msg}`);
  };

  const gov = (contract && contract.governance) || {};
  overdue(gov.next_review, "governance.next_review",
    "is in the past — governance review overdue");

  if (status !== "retired") {
    overdue(lifecycle.retirement_date, "lifecycle.retirement_date",
      `has passed but status is '${status}' — agent should be retired`);
  }
  const retirement = lifecycle.retirement || {};
  if (status !== "retired") {
    overdue(retirement.sunset_date, "lifecycle.retirement.sunset_date",
      `has passed but status is '${status}' — agent should be retired`);
  }
  overdue(retirement.planned_review_date, "lifecycle.retirement.planned_review_date",
    "has passed — retirement decision review overdue");

  return warnings;
}

// ---------------------------------------------------------------------------
// Core validation
// ---------------------------------------------------------------------------

/**
 * Build a configured Ajv instance. A fresh instance is created per call so that
 * re-loading the schema (a new object with the same `$id`) never trips Ajv's
 * duplicate-`$id` guard.
 * @returns {import("ajv").default}
 */
function makeAjv() {
  const ajv = new Ajv({ allErrors: true, strict: false });
  addFormats(ajv);
  return ajv;
}

/**
 * Validate a contract file and gather errors, warnings, notices, and the parsed
 * contract in one pass.
 * @returns {{ file: string, errors: string[], warnings: string[], notices: string[], contract: object|null }}
 */
function evaluateFile(filepath, schema, today) {
  const result = { file: filepath, errors: [], warnings: [], notices: [], contract: null };

  if (!fs.existsSync(filepath)) {
    result.errors.push(`File not found: ${filepath}`);
    return result;
  }

  let contract;
  try {
    contract = yaml.load(fs.readFileSync(filepath, "utf-8"));
  } catch (e) {
    result.errors.push(`YAML parse error: ${e.message}`);
    return result;
  }

  if (!contract || typeof contract !== "object" || Array.isArray(contract)) {
    result.errors.push("File does not contain a YAML mapping (expected top-level object)");
    return result;
  }

  result.contract = contract;

  const validate = makeAjv().compile(schema);
  if (!validate(contract) && validate.errors) {
    for (const err of validate.errors) {
      const fieldPath = err.instancePath || "(root)";
      result.errors.push(`Schema: [${fieldPath}] ${err.message}`);
    }
  }

  for (const e of semanticChecks(contract)) result.errors.push(`Semantic: ${e}`);
  for (const w of lifecycleChecks(contract, today)) result.warnings.push(w);
  const notice = schemaVersionNotice(contract);
  if (notice) result.notices.push(notice);

  return result;
}

/** A result passes if it has no errors (and, under strict, no warnings). */
function resultPassed(result, strict) {
  if (result.errors.length) return false;
  if (strict && result.warnings.length) return false;
  return true;
}

/**
 * Validate a single YAML contract file (errors only; warnings never fail here).
 * Kept stable for callers that predate v2.
 * @returns {{ passed: boolean, errors: string[] }}
 */
function validateFile(filepath, schema) {
  const r = evaluateFile(filepath, schema);
  return { passed: r.errors.length === 0, errors: r.errors };
}

// ---------------------------------------------------------------------------
// Path expansion — files, directories (recursive *.yaml/*.yml), and literals.
// (Shell globs are expanded by the shell before Node sees them.)
// ---------------------------------------------------------------------------

const YAML_EXTS = [".yaml", ".yml"];

function walkYaml(dir) {
  const found = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      found.push(...walkYaml(full));
    } else if (YAML_EXTS.includes(path.extname(entry.name).toLowerCase())) {
      found.push(full);
    }
  }
  return found;
}

/**
 * @param {string[]} inputs
 * @returns {string[]} de-duplicated, sorted contract file paths
 */
function expandPaths(inputs) {
  const collected = [];
  for (const raw of inputs) {
    if (fs.existsSync(raw) && fs.statSync(raw).isDirectory()) {
      collected.push(...walkYaml(raw));
    } else {
      collected.push(raw);
    }
  }
  return [...new Set(collected.map((p) => path.normalize(p)))].sort();
}

module.exports = {
  schemaCandidatePaths,
  loadSchema,
  checkEmail,
  semanticChecks,
  lifecycleChecks,
  schemaVersionOf,
  schemaVersionNotice,
  evaluateFile,
  resultPassed,
  validateFile,
  expandPaths,
  parseIsoDate,
  EMAIL_RE,
};
