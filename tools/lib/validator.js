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
 * Validate a single YAML contract file.
 * @param {string} filepath
 * @param {object} schema
 * @returns {{ passed: boolean, errors: string[] }}
 */
function validateFile(filepath, schema) {
  const errors = [];

  if (!fs.existsSync(filepath)) {
    return { passed: false, errors: [`File not found: ${filepath}`] };
  }

  let contract;
  try {
    contract = yaml.load(fs.readFileSync(filepath, "utf-8"));
  } catch (e) {
    return { passed: false, errors: [`YAML parse error: ${e.message}`] };
  }

  if (!contract || typeof contract !== "object" || Array.isArray(contract)) {
    return {
      passed: false,
      errors: ["File does not contain a YAML mapping (expected top-level object)"],
    };
  }

  const validate = makeAjv().compile(schema);
  if (!validate(contract) && validate.errors) {
    for (const err of validate.errors) {
      const fieldPath = err.instancePath || "(root)";
      errors.push(`Schema: [${fieldPath}] ${err.message}`);
    }
  }

  for (const e of semanticChecks(contract)) errors.push(`Semantic: ${e}`);

  return { passed: errors.length === 0, errors };
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
  validateFile,
  expandPaths,
  EMAIL_RE,
};
