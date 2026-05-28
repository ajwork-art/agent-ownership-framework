#!/usr/bin/env node
/**
 * Agent Ownership Framework (AOF) — Contract Validator (Node.js)
 *
 * Validates AOF v1 agent ownership contract YAML files against the JSON Schema
 * and performs additional semantic checks beyond what JSON Schema can enforce.
 *
 * Usage:
 *   node validate-contract.js <file> [<file> ...]
 *   node validate-contract.js examples/support-agent.yaml
 *   node validate-contract.js examples/*.yaml
 *   node validate-contract.js --help
 *
 * Exit codes:
 *   0 — all files valid
 *   1 — one or more files failed validation
 *
 * @author Anitha Jagadeesh — Enterprise Data AI Realities
 * @license MIT
 */

"use strict";

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------------------
// Dependency checks
// ---------------------------------------------------------------------------

let yaml, Ajv, chalk;

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
  chalk = require("chalk");
} catch {
  // Graceful fallback: no colors
  chalk = {
    green: (s) => s,
    red: (s) => s,
    yellow: (s) => s,
    bold: (s) => s,
  };
}

// ---------------------------------------------------------------------------
// Output helpers
// ---------------------------------------------------------------------------

/** Print a pass result */
const ok = (msg) => `${chalk.green("✓")} ${msg}`;

/** Print a fail result */
const fail = (msg) => `${chalk.red("✗")} ${msg}`;

/** Print a warning */
const warn = (msg) => `${chalk.yellow("!")} ${msg}`;

// ---------------------------------------------------------------------------
// Schema loading
// ---------------------------------------------------------------------------

/**
 * Load the AOF v1 JSON Schema from the schema directory.
 * Resolves the path relative to this script's location.
 * @returns {object} Parsed JSON Schema
 */
function loadSchema() {
  const scriptDir = __dirname;
  const schemaPath = path.resolve(
    scriptDir,
    "..",
    "schema",
    "v1",
    "agent-ownership-contract.schema.json"
  );

  if (!fs.existsSync(schemaPath)) {
    throw new Error(
      `Schema not found at: ${schemaPath}\n` +
      "Make sure you are running from the repository root or tools/ directory."
    );
  }

  const raw = fs.readFileSync(schemaPath, "utf-8");
  return JSON.parse(raw);
}

// ---------------------------------------------------------------------------
// Additional semantic checks
// ---------------------------------------------------------------------------

const EMAIL_RE = /^[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+$/;

/**
 * Validate an email address.
 * @param {string} value
 * @param {string} fieldPath
 * @returns {string|null} Error message or null if valid
 */
function checkEmail(value, fieldPath) {
  if (!EMAIL_RE.test(value)) {
    return `${fieldPath}: '${value}' is not a valid email address`;
  }
  return null;
}

/**
 * Perform semantic checks beyond JSON Schema validation.
 * @param {object} contract - Parsed YAML contract
 * @returns {string[]} Array of error messages (empty means all checks passed)
 */
function semanticChecks(contract) {
  const errors = [];

  // ---- SLA checks ---------------------------------------------------------
  const sla = contract.sla || {};
  if (typeof sla === "object") {
    const availability = sla.availability;
    if (availability !== undefined) {
      if (typeof availability !== "number") {
        errors.push(
          "sla.availability: must be a number (e.g., 99.9), not a string"
        );
      } else if (availability < 0 || availability > 100) {
        errors.push(
          `sla.availability: ${availability} is out of range — must be 0 to 100`
        );
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

  // ---- Escalation path checks -------------------------------------------
  const ownership = contract.ownership || {};
  const escalation = ownership.escalation_path || [];
  if (Array.isArray(escalation) && escalation.length > 0) {
    const levels = [];
    escalation.forEach((entry, i) => {
      if (entry && typeof entry === "object") {
        if (entry.level !== undefined) {
          levels.push(entry.level);
        }
        if (entry.email && typeof entry.email === "string") {
          const err = checkEmail(
            entry.email,
            `ownership.escalation_path[${i}].email`
          );
          if (err) errors.push(err);
        }
      }
    });

    // Levels must be sequential starting at 1
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

  // ---- Incident contact email -------------------------------------------
  const accountability = contract.accountability || {};
  if (typeof accountability === "object") {
    const incidentContact = accountability.incident_contact;
    if (incidentContact && typeof incidentContact === "string") {
      const err = checkEmail(incidentContact, "accountability.incident_contact");
      if (err) errors.push(err);
    }
  }

  // ---- Kill switch owner email ------------------------------------------
  const risk = contract.risk || {};
  if (typeof risk === "object") {
    const killSwitchOwner = risk.kill_switch_owner;
    if (killSwitchOwner && typeof killSwitchOwner === "string") {
      const err = checkEmail(killSwitchOwner, "risk.kill_switch_owner");
      if (err) errors.push(err);
    }
  }

  // ---- Primary owner email ---------------------------------------------
  const primaryOwner = ownership.primary_owner || {};
  if (typeof primaryOwner === "object" && primaryOwner.email) {
    const err = checkEmail(
      primaryOwner.email,
      "ownership.primary_owner.email"
    );
    if (err) errors.push(err);
  }

  return errors;
}

// ---------------------------------------------------------------------------
// Core validation
// ---------------------------------------------------------------------------

/**
 * Validate a single YAML contract file.
 * @param {string} filepath - Path to the YAML file
 * @param {object} schema - Parsed JSON Schema
 * @param {Ajv} ajv - Configured AJV validator instance
 * @param {boolean} verbose - Print individual check results
 * @returns {{ passed: boolean, errors: string[] }}
 */
function validateFile(filepath, schema, ajv, verbose) {
  const errors = [];

  // 1. File existence
  if (!fs.existsSync(filepath)) {
    return { passed: false, errors: [`File not found: ${filepath}`] };
  }

  // 2. YAML parse
  let contract;
  try {
    const raw = fs.readFileSync(filepath, "utf-8");
    contract = yaml.load(raw);
  } catch (e) {
    return { passed: false, errors: [`YAML parse error: ${e.message}`] };
  }

  if (!contract || typeof contract !== "object" || Array.isArray(contract)) {
    return {
      passed: false,
      errors: ["File does not contain a YAML mapping (expected top-level object)"],
    };
  }

  if (verbose) {
    console.log(`  ${ok("YAML parsed successfully")}`);
  }

  // 3. JSON Schema validation
  const validate = ajv.compile(schema);
  const valid = validate(contract);
  if (!valid && validate.errors) {
    for (const err of validate.errors) {
      const fieldPath = err.instancePath || "(root)";
      errors.push(`Schema: [${fieldPath}] ${err.message}`);
    }
  } else if (verbose) {
    console.log(`  ${ok("JSON Schema validation passed")}`);
  }

  // 4. Semantic checks
  const semErrors = semanticChecks(contract);
  if (semErrors.length > 0) {
    semErrors.forEach((e) => errors.push(`Semantic: ${e}`));
  } else if (verbose) {
    console.log(`  ${ok("Semantic checks passed")}`);
  }

  return { passed: errors.length === 0, errors };
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

/**
 * Print usage information and exit.
 */
function printHelp() {
  console.log(`
AOF Contract Validator (Node.js) v1.0.0
Agent Ownership Framework — https://github.com/anitha-jagadeesh/agent-ownership-framework

Usage:
  node validate-contract.js <file> [<file> ...]
  node validate-contract.js examples/support-agent.yaml
  node validate-contract.js examples/*.yaml

Options:
  --help     Show this help message
  --verbose  Print each individual check result

Examples:
  node validate-contract.js examples/support-agent.yaml
  node validate-contract.js examples/fraud-detection-agent.yaml --verbose
  node validate-contract.js examples/*.yaml

Exit codes:
  0  All files valid
  1  One or more files failed validation
`);
  process.exit(0);
}

/**
 * Main entry point.
 */
function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    printHelp();
  }

  const verbose = args.includes("--verbose");
  const files = args.filter((a) => !a.startsWith("--"));

  if (files.length === 0) {
    console.error(fail("No files specified. Run with --help for usage."));
    process.exit(1);
  }

  // Load schema
  let schema;
  try {
    schema = loadSchema();
  } catch (e) {
    console.error(fail(`Cannot load schema: ${e.message}`));
    process.exit(1);
  }

  // Configure AJV (draft-07, collect all errors)
  const ajv = new Ajv({ allErrors: true, strict: false });

  const results = [];
  let anyFailed = false;

  for (const filepath of files) {
    if (verbose) {
      console.log(`\n${chalk.bold(`Validating: ${filepath}`)}`);
    }

    const { passed, errors } = validateFile(filepath, schema, ajv, verbose);

    if (!passed) anyFailed = true;

    results.push({ file: filepath, passed, errors });

    const filename = path.basename(filepath);
    if (passed) {
      console.log(ok(chalk.bold(filename)));
    } else {
      console.log(fail(chalk.bold(filename)));
      for (const err of errors) {
        console.log(`    ${chalk.red("→")} ${err}`);
      }
    }
  }

  // Summary
  const total = results.length;
  const passedCount = results.filter((r) => r.passed).length;
  const failedCount = total - passedCount;

  console.log();
  if (failedCount === 0) {
    console.log(ok(`All ${total} contract(s) valid`));
  } else {
    console.log(fail(`${failedCount}/${total} contract(s) failed validation`));
  }

  process.exit(anyFailed ? 1 : 0);
}

main();
