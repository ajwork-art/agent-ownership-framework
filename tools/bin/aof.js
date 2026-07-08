#!/usr/bin/env node
"use strict";
/**
 * aof — Agent Ownership Framework CLI (Node.js).
 *
 * Verbs mirror the Python CLI:
 *   aof validate <path...> [--strict] [--output text|json]
 *   aof check <file>     (stub — use the Python CLI for the full boundary report)
 *   aof create <name>    (stub — use the Python CLI)
 *   aof export <file>    (stub — Phase 3)
 *
 * `<path>` for validate may be a file or a directory (searched recursively for
 * *.yaml / *.yml). AOF performs deployment-time contract validation; it does
 * not enforce policy at runtime.
 *
 * @license MIT
 */

const path = require("path");

let chalk;
try {
  const chalkModule = require("chalk");
  chalk = chalkModule.default || chalkModule;
  if (typeof chalk.green !== "function") throw new Error("chalk unavailable");
} catch {
  chalk = { green: (s) => s, red: (s) => s, yellow: (s) => s, bold: (s) => s };
}

const {
  loadSchema,
  evaluateFile,
  resultPassed,
  schemaVersionOf,
  expandPaths,
} = require("../lib/validator");
const pkg = require("../package.json");

const ok = (m) => `${chalk.green("✓")} ${m}`;
const fail = (m) => `${chalk.red("✗")} ${m}`;
const warn = (m) => `${chalk.yellow("!")} ${m}`;

function printHelp() {
  console.log(`
aof ${pkg.version} — Agent Ownership Framework CLI (deployment-time validation)

Usage:
  aof validate <path...> [--strict] [--output text|json]
  aof --version

validate:
  <path> may be a file or a directory (searched recursively for *.yaml/*.yml).
  --strict   Fail (non-zero) if no contracts are found OR any contract has
             lifecycle warnings (e.g. a governance review date in the past).
  --output   text (default) or json.

The Python CLI (pip install aof-validate) additionally provides:
  aof scan · aof diff · aof verify · aof check · aof create · aof export

Exit codes: 0 = valid, 1 = failed / not found (strict), 2 = Python-CLI command.
`);
}

function cmdValidate(args) {
  const strict = args.includes("--strict");
  let output = "text";
  const oi = args.indexOf("--output");
  if (oi !== -1 && args[oi + 1]) output = args[oi + 1];
  const paths = args.filter(
    (a, i) => !a.startsWith("--") && !(i > 0 && args[i - 1] === "--output")
  );

  if (paths.length === 0) {
    console.error(fail("No paths given. Usage: aof validate <path...>"));
    return 1;
  }

  let schema;
  try {
    schema = loadSchema();
  } catch (e) {
    console.error(fail(`Cannot load schema: ${e.message}`));
    return 1;
  }

  const files = expandPaths(paths);
  if (files.length === 0) {
    const msg = `No contract files (*.yaml/*.yml) found in: ${paths.join(", ")}`;
    if (strict) {
      console.error(fail(msg));
      return 1;
    }
    console.log(warn(msg));
    return 0;
  }

  const results = [];
  let anyFailed = false;
  for (const filepath of files) {
    const r = evaluateFile(filepath, schema);
    const passed = resultPassed(r, strict);
    if (!passed) anyFailed = true;
    results.push({
      file: filepath,
      passed,
      schema_version: r.contract ? schemaVersionOf(r.contract) : null,
      errors: r.errors,
      warnings: r.warnings,
      notices: r.notices,
    });
    if (output === "text") {
      const name = path.basename(filepath);
      console.log(passed ? ok(chalk.bold(name)) : fail(chalk.bold(name)));
      for (const err of r.errors) console.log(`    ${chalk.red("→")} ${err}`);
      const tag = strict ? "" : chalk.yellow(" (fails under --strict)");
      for (const w of r.warnings) console.log(`    ${chalk.yellow("!")} ${w}${tag}`);
      for (const n of r.notices) console.log(`    ${chalk.yellow("·")} ${n}`);
    }
  }

  const total = results.length;
  const failed = results.filter((r) => !r.passed).length;
  const warned = results.filter((r) => r.warnings.length).length;
  if (output === "json") {
    console.log(
      JSON.stringify(
        { aof: pkg.version, strict, total, passed: total - failed, failed, with_warnings: warned, results },
        null,
        2
      )
    );
  } else {
    console.log();
    if (failed === 0) {
      const suffix = warned && !strict ? ` (${warned} with warnings)` : "";
      console.log(ok(`All ${total} contract(s) valid${suffix}`));
    } else {
      console.log(fail(`${failed}/${total} contract(s) failed validation`));
    }
  }

  return anyFailed ? 1 : 0;
}

function cmdStub(verb) {
  console.log(
    warn(
      `\`aof ${verb}\` is available in the Python CLI. ` +
        `Install it with \`pip install aof-validate\` and run \`aof ${verb}\`. ` +
        "The Node CLI implements \`aof validate\` (including lifecycle checks and --strict)."
    )
  );
  return 2;
}

function main() {
  const argv = process.argv.slice(2);
  if (argv.length === 0 || argv.includes("--help") || argv.includes("-h")) {
    printHelp();
    process.exit(0);
  }
  if (argv[0] === "--version") {
    console.log(`aof ${pkg.version}`);
    process.exit(0);
  }

  const verb = argv[0];
  const rest = argv.slice(1);
  let code;
  switch (verb) {
    case "validate":
      code = cmdValidate(rest);
      break;
    case "check":
    case "create":
    case "scan":
    case "diff":
    case "verify":
    case "export":
      code = cmdStub(verb);
      break;
    default:
      console.error(fail(`Unknown command: ${verb}`));
      printHelp();
      code = 1;
  }
  process.exit(code);
}

main();
