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

const { loadSchema, validateFile, expandPaths } = require("../lib/validator");
const pkg = require("../package.json");

const ok = (m) => `${chalk.green("✓")} ${m}`;
const fail = (m) => `${chalk.red("✗")} ${m}`;
const warn = (m) => `${chalk.yellow("!")} ${m}`;

function printHelp() {
  console.log(`
aof ${pkg.version} — Agent Ownership Framework CLI (deployment-time validation)

Usage:
  aof validate <path...> [--strict] [--output text|json]
  aof check <file>       (stub — full boundary report is in the Python CLI)
  aof create <name>      (stub — use the Python CLI)
  aof export <file>      (stub — planned for a future release)
  aof --version

validate:
  <path> may be a file or a directory (searched recursively for *.yaml/*.yml).
  --strict   Fail (non-zero) if no contracts are found.
  --output   text (default) or json.

Exit codes: 0 = valid, 1 = failed / not found (strict), 2 = not implemented.
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
    const { passed, errors } = validateFile(filepath, schema);
    if (!passed) anyFailed = true;
    results.push({ file: filepath, passed, errors });
    if (output === "text") {
      const name = path.basename(filepath);
      if (passed) {
        console.log(ok(chalk.bold(name)));
      } else {
        console.log(fail(chalk.bold(name)));
        for (const err of errors) console.log(`    ${chalk.red("→")} ${err}`);
      }
    }
  }

  const total = results.length;
  const failed = results.filter((r) => !r.passed).length;
  if (output === "json") {
    console.log(
      JSON.stringify(
        {
          aof_validator: pkg.version,
          total,
          passed: total - failed,
          failed,
          results,
        },
        null,
        2
      )
    );
  } else {
    console.log();
    console.log(failed === 0 ? ok(`All ${total} contract(s) valid`) : fail(`${failed}/${total} contract(s) failed validation`));
  }

  return anyFailed ? 1 : 0;
}

function cmdStub(verb) {
  if (verb === "export") {
    console.log(warn("`aof export` is not implemented yet — planned for a future release."));
  } else {
    console.log(
      warn(
        `\`aof ${verb}\` is not implemented in the Node CLI. ` +
          `Use the Python CLI (pip install aof-validate) for \`aof ${verb}\`.`
      )
    );
  }
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
