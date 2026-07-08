# Changelog

All notable changes to the Agent Ownership Framework (AOF) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-07-08

Second major release: the validator becomes an installable `aof` CLI (Python + Node) and
a GitHub Action; adds v2 governance capabilities (lifecycle enforcement, `aof scan`,
`aof diff`, `aof verify`, `aof export`) and the optional additive `schema_version` field.
Fully backward compatible — every valid v1 contract still validates. AOF remains
deployment-time validation and generates policy inputs; it does not enforce at runtime.

### Added

_Packaging (Phase 2)_
- **Installable Python package** `aof-validate` (`tools/pyproject.toml`) exposing the
  `aof` command with `validate`, `check`, `create`, and `export`. `aof validate`
  accepts a file, a directory (searched recursively), or a glob, and supports
  `--strict` and `--output json`. The JSON Schema is bundled as package data (a test
  asserts it stays byte-identical to `schema/v1/`).
- **Installable Node package** `aof-validate` (`tools/package.json`) with an `aof` bin
  implementing `aof validate` (lifecycle checks + `--strict`); the richer verbs live in
  the Python CLI.
- **Composite GitHub Action** (`action.yml`) that runs `aof validate` against a
  configurable `contracts` directory, with `strict` and `python-version` inputs, plus
  README usage and GitHub Marketplace listing instructions.
- README **Installation** and **GitHub Action** sections.

_v2 capabilities (Phase 3)_
- **Optional `schema_version` field** (additive). Absent means `1.0`; a valid v1
  contract still validates and receives an informational notice (never an error).
- **Lifecycle enforcement** in `aof validate`: warns when `governance.next_review`,
  `lifecycle.retirement_date`, `lifecycle.retirement.sunset_date`, or
  `lifecycle.retirement.planned_review_date` have passed. `--strict` promotes these
  warnings to CI-blocking failures. Implemented in both the Python and Node validators.
- **`aof scan`** — recursive fleet inventory with a human-readable table and `--json`
  (per-contract status: valid/unsigned/expired/invalid, owners, coverage summary).
- **`aof diff <old> <new>`** — semantic diff classifying changes as material
  (`authority`, `data`, `ownership.escalation_path`, `signoff`) vs cosmetic;
  `--require-reapproval` exits non-zero on material changes with an unchanged signoff.
- **`aof verify`** — optional detached GPG signature verification (no PKI, no private
  keys). GPG implemented; a Sigstore/cosign recipe is documented in docs/INTEGRATION.md.
- **`aof export --format markdown|a2a-card|opa`** — ownership card (markdown), an
  experimental A2A Agent Card mapping (verified against a2a-protocol.org, v1.0.0), and
  an OPA/Rego policy **stub** with TODO markers. AOF generates policy inputs; it does
  not enforce at runtime.
- **Test suites**: pytest (`tools/tests/`) and `node:test` (`tools/test/`), both run in CI.

_Documentation & examples (Phase 4)_
- **MIGRATION.md** — v1 → v2 guide (v1 stays valid, opting into v2 fields, adopting signing).
- **ROADMAP.md** — placeholder for the maintainer, capturing known future work.
- **Two v2 example contracts**: `examples/retention-sweeper-agent.yaml` (lifecycle dates +
  four-role sign-off) and `examples/orchestrator-agent.yaml` (an orchestrator modeled via
  `dependencies`, with first-class multi-agent modeling noted as future work).
- README **v1 → v2** section, **CLI reference**, and refreshed badges.

### Changed
- CI installs the packages, runs both test suites, exercises the `aof` CLI against every
  example and the annotated schema example, and runs the composite action end-to-end.
- The standalone `tools/validate-contract.py` and `tools/validate-contract.js` are now
  thin **deprecated** shims that delegate to the packaged core and print a deprecation
  notice; their historical interfaces still work.
- `schema_version` added to the JSON Schema (and the bundled copy) as an optional
  property; the annotated example and the five example contracts had their governance
  review dates refreshed so they are current.
- The `a2a-card` export note now states explicitly that it is an experimental **draft
  mapping**, not a publish-ready Agent Card.
- `examples/README.md` modernized to `aof` commands and real schema field names.

### Fixed
- Markdown exporter now renders escalation paths with their actual numeric levels
  (`1.`, `2.`, `3.`) instead of a repeated `1.`.

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

[Unreleased]: https://github.com/ajwork-art/agent-ownership-framework/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/ajwork-art/agent-ownership-framework/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/ajwork-art/agent-ownership-framework/releases/tag/v1.0.0
