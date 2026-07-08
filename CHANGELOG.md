# Changelog

All notable changes to the Agent Ownership Framework (AOF) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Installable Python package** `aof-validate` (`tools/pyproject.toml`) exposing the
  `aof` command with `validate`, `check`, `create`, and a stubbed `export` subcommand.
  `aof validate` accepts a file, a directory (searched recursively), or a glob, and
  supports `--strict` and `--output json`. The JSON Schema is bundled as package data
  (a test asserts it stays byte-identical to `schema/v1/`).
- **Installable Node package** `aof-validate` (`tools/package.json`) with an `aof` bin
  exposing the matching verbs (`validate` implemented; `check`/`create`/`export` stubbed).
- **Composite GitHub Action** (`action.yml`) that runs `aof validate` against a
  configurable `contracts` directory, with `strict` and `python-version` inputs, plus
  README usage and GitHub Marketplace listing instructions.
- **Test suites**: pytest (`tools/tests/`) and `node:test` (`tools/test/`), both run in CI.
- README **Installation** and **GitHub Action** sections.

### Changed
- CI now installs the packages, runs both test suites, exercises the `aof` CLI against
  every example and the annotated schema example, and runs the composite action
  end-to-end.
- The standalone `tools/validate-contract.py` and `tools/validate-contract.js` are now
  thin **deprecated** shims that delegate to the packaged core and print a deprecation
  notice; their historical interfaces still work.

### Removed
- `tools/setup.py` (superseded by `tools/pyproject.toml`) and the standalone
  `tools/aof` script (its logic moved into the `aof` package).

## [1.0.0] - 2026-07-07

Initial public release of the Agent Ownership Framework — an open standard for
machine-readable agent ownership contracts and deployment-time contract validation.

### Added
- **Schema** — JSON Schema (draft-07) for the `AgentOwnershipContract`, covering the
  eight governance boundaries (purpose, ownership, authority, data, incident response,
  governance, lifecycle, compliance) plus risk, signoff, dependencies, and SLA. Ships
  with an annotated, field-by-field reference example.
- **Examples** — Five production-realistic contracts: support, operations,
  fraud-detection, risk-analysis, and internal-tool agents, spanning low to critical
  risk tiers.
- **Validators** — Python (`validate-contract.py`) and Node.js (`validate-contract.js`)
  validators that check contracts against the JSON Schema and apply additional semantic
  checks. Both enforce `date` and `email` formats (the Node validator via `ajv-formats`)
  in addition to SLA ranges and sequential escalation levels.
- **`aof` CLI** — `validate`, `create`, and `check` commands, including a human-readable
  eight-boundary governance checklist.
- **Continuous integration** — `.github/workflows/ci.yml` runs the Python and Node.js
  validator suites, validates every example contract and the annotated schema example,
  and runs the `aof check` governance-boundary checklist on every push and pull request.
  The README carries a live CI status badge.
- **CI/CD integration** — GitHub Actions, GitLab CI, and Terraform examples for enforcing
  contract validation in deployment pipelines.
- **Templates** — Blank contract template, pre-launch checklist, week-by-week
  implementation guide, and non-technical field explanations.
- **Documentation** — Framework concepts, principles, complete schema reference,
  integration guide, compliance mappings, troubleshooting, FAQ, and the AOF ecosystem
  diagram.
- **This `CHANGELOG.md`.**

[Unreleased]: https://github.com/ajwork-art/agent-ownership-framework/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ajwork-art/agent-ownership-framework/releases/tag/v1.0.0
