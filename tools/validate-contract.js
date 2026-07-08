#!/usr/bin/env node
"use strict";
/**
 * DEPRECATED — Agent Ownership Framework (AOF) standalone validator (Node.js).
 *
 * Preserved for backward compatibility. Delegates to the shared core in
 * lib/validator.js. Please migrate to the packaged CLI:
 *
 *   npm install -g aof-validate     # installs the `aof` command
 *   aof validate <path>             # file or directory
 *
 * The legacy interface below (positional files, --verbose) still works.
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

const { loadSchema, validateFile, expandPaths } = require("./lib/validator");

const ok = (m) => `${chalk.green("✓")} ${m}`;
const fail = (m) => `${chalk.red("✗")} ${m}`;

function main() {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    console.log("Usage: node validate-contract.js <file> [file ...]");
    console.log("Deprecated — use `aof validate <path>` (npm install -g aof-validate).");
    process.exit(0);
  }

  console.error(
    `${chalk.yellow("!")} validate-contract.js is deprecated. ` +
      "Install the package and use `aof validate <path>` (npm install -g aof-validate)."
  );

  const files = expandPaths(args.filter((a) => !a.startsWith("--")));
  if (files.length === 0) {
    console.error(fail("No files specified."));
    process.exit(1);
  }

  let schema;
  try {
    schema = loadSchema();
  } catch (e) {
    console.error(fail(`Cannot load schema: ${e.message}`));
    process.exit(1);
  }

  let failed = 0;
  for (const filepath of files) {
    const { passed, errors } = validateFile(filepath, schema);
    if (!passed) failed += 1;
    const name = path.basename(filepath);
    if (passed) {
      console.log(ok(chalk.bold(name)));
    } else {
      console.log(fail(chalk.bold(name)));
      for (const err of errors) console.log(`    ${chalk.red("→")} ${err}`);
    }
  }

  console.log();
  const total = files.length;
  console.log(failed === 0 ? ok(`All ${total} contract(s) valid`) : fail(`${failed}/${total} contract(s) failed validation`));
  process.exit(failed > 0 ? 1 : 0);
}

main();
