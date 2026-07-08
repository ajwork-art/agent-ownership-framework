# Tools

Validation and CLI tooling for AOF v1 agent ownership contracts.

---

## AOF CLI (`aof`)

`aof` is an installable command that wraps the validator and adds a governance
boundary checklist. It is packaged for both Python (`aof-validate` on PyPI) and
Node.js (`aof-validate` on npm); both install a single `aof` command with the same
verbs. AOF performs **deployment-time** validation and does not enforce policy at
runtime.

**Requirements:** Python 3.8+ (pyyaml, jsonschema) or Node.js 18+.

### Install

```bash
# Python — from source today; `pip install aof-validate` once published
pip install ./tools

# Node.js — from source today; `npm install -g aof-validate` once published
npm install -g ./tools
```

The bare `aof` name is taken by unrelated projects on PyPI and npm, so the
distribution is named **`aof-validate`**; the installed command is still `aof`.

### Run without installing

```bash
cd tools
pip install -r requirements.txt   # or: pip install -e '.[dev]'

python -m aof validate ../examples/support-agent.yaml
python -m aof create  my-payment-agent.yaml
python -m aof check   my-payment-agent.yaml

# Node equivalent:
node bin/aof.js validate ../examples/support-agent.yaml
```

The `validate` verb accepts a file, a directory (searched recursively for
`*.yaml` / `*.yml`), or a glob, and supports `--strict` and `--output json`.

### v2 commands (Python CLI)

All are deployment-time tooling. The exporters generate policy **inputs**; AOF does
not enforce policy at runtime.

| Command | Purpose |
|---------|---------|
| `aof validate --strict` | Fail on lifecycle warnings (stale `next_review`, past retirement/sunset dates) — CI-blocking |
| `aof scan <dir>` | Fleet inventory: per-contract status (valid/unsigned/expired/invalid), owners, coverage stats (`--json`) |
| `aof diff <old> <new>` | Semantic diff; classify **material** (authority/data/escalation/signoff) vs cosmetic; `--require-reapproval` |
| `aof verify <file>` | Optional detached GPG signature verification (never required; no PKI) |
| `aof export --format markdown\|a2a-card\|opa <file>` | Ownership card, experimental A2A card, or Rego policy stub |

The Node CLI implements `aof validate` (with lifecycle checks and `--strict`); the
commands above are provided by the Python package.

---

### Command: `aof validate`

Validates one or more contract files against the AOF JSON Schema and semantic rules.

```bash
# Single file
aof validate my-agent.yaml

# Multiple files
aof validate examples/support-agent.yaml examples/fraud-detection-agent.yaml

# Glob (all examples)
aof validate examples/*.yaml

# Verbose — shows each check result
aof validate --verbose my-agent.yaml
```

**Example output:**

```
✓ support-agent.yaml
✓ fraud-detection-agent.yaml
✗ my-broken-contract.yaml
    → Schema: [sla.availability] '99.9%' is not of type 'number'
    → Semantic: sla.max_latency_ms: must be an integer

✗ 1/3 contract(s) failed validation
```

Exit code `0` = all valid, `1` = one or more failed.

---

### Command: `aof create`

Copies the blank contract template to a new file, ready to fill in.

```bash
aof create my-payment-agent.yaml
aof create contracts/fraud-detection-agent.yaml
```

**Example output:**

```
✓ Created: my-payment-agent.yaml

Next steps:
  1. Open my-payment-agent.yaml and replace all placeholder values
  2. Validate the schema:      aof validate my-payment-agent.yaml
  3. Check all 8 boundaries:   aof check my-payment-agent.yaml

Reference example: schema/v1/agent-ownership-contract.example.yaml
```

---

### Command: `aof check`

Validates the schema and checks all eight AOF governance boundaries, showing a
human-readable checklist with pass/fail per item.

```bash
aof check my-agent.yaml
aof check examples/fraud-detection-agent.yaml
```

**Example output (fully complete contract):**

```
Contract Boundary Check: fraud-detection-agent.yaml
══════════════════════════════════════════════════════

  Schema validation:  ✓ PASS

  ✓ Boundary 1 — Purpose
      ✓ Business purpose: 455 chars
      ✓ Success metrics: 3 defined
      ✓ Out-of-scope list: 3 explicit exclusion(s)

  ✓ Boundary 2 — Ownership
      ✓ Domain owner: Michael Chang (michael.chang@example.com)
      ✓ Technical owner: Priya Sharma (priya.sharma@example.com)

  ✓ Boundary 3 — Authority
      ✓ Autonomous decisions: 2 defined
      ✓ Prohibited actions: 3 defined
      ✓ Escalation triggers: 3 defined
      ✓ Override mechanism: 2 pause role(s), override role named

  ✓ Boundary 4 — Data
      ✓ Permitted sources: 4 defined
      ✓ Prohibited sources: 4 defined
      ✓ Sensitive data handling rules: 2 field(s) masked

  ✓ Boundary 5 — Escalation Path
      ✓ Escalation path: 3 levels defined [1, 2, 3]

  ✓ Boundary 6 — Incident Response
      ✓ Primary investigator: technical_owner (Priya Sharma)
      ✓ Investigation scope: 5 questions defined
      ✓ Communication owners: customer, stakeholder, and compliance defined

  ✓ Boundary 7 — Governance
      ✓ Review cadence: monthly
      ✓ Change control board: Financial Crime Risk Committee
      ✓ Approval required for: 4 change type(s)
      ✓ Signoff: Michael Chang (domain) and Priya Sharma (technical)

  ✓ Boundary 8 — Compliance
      ✓ Compliance frameworks: PCI-DSS, BSA-AML, SOX, GLBA
      ✓ Data classification: highly-restricted
      ✓ Audit log required: true

──────────────────────────────────────────────────────
  ✓ All 8 boundaries satisfied — contract is governance-complete
```

The eight boundaries checked:

| # | Boundary | Fields checked |
|---|----------|----------------|
| 1 | Purpose | `purpose.business_purpose`, `success_metrics`, `out_of_scope` |
| 2 | Ownership | `ownership.domain_owner`, `technical_owner` (name + email) |
| 3 | Authority | `autonomous_decisions`, `prohibited_actions`, `escalation_triggers`, `override_mechanism` |
| 4 | Data | `data.permitted_sources`, `prohibited_sources`, `sensitive_data_handling` |
| 5 | Escalation Path | `ownership.escalation_path` (ordered levels) |
| 6 | Incident Response | `incident_response.investigator_primary`, `investigation_scope`, `communication` |
| 7 | Governance | `governance.review_cadence`, `change_control_board`, `approval_required_for`, `signoff` |
| 8 | Compliance | `compliance.frameworks`, `data_classification`, `audit_log_required` |

Exit code `0` = schema valid and all 8 boundaries satisfied, `1` = any issue found.

---

## Python Validator (`validate-contract.py`) — deprecated

> **Deprecated.** This standalone script is kept for backward compatibility and now
> prints a deprecation notice and delegates to the `aof` package. Use `aof validate`
> instead. The core validation logic lives in `aof/validator.py`.

**Requirements:** Python 3.8+, pyyaml, jsonschema

### Install

```bash
cd tools
pip install -r requirements.txt
```

### Usage

```bash
# Validate a single file
python validate-contract.py examples/support-agent.yaml

# Validate multiple files
python validate-contract.py examples/support-agent.yaml examples/fraud-detection-agent.yaml

# Validate all examples using glob
python validate-contract.py examples/*.yaml

# Verbose output (shows each check result)
python validate-contract.py --verbose examples/fraud-detection-agent.yaml

# Machine-readable JSON output
python validate-contract.py --output json examples/support-agent.yaml

# Show help
python validate-contract.py --help
```

### Example Output

```
✓ support-agent.yaml
✓ operations-agent.yaml
✗ my-broken-contract.yaml
    → Schema: [sla.availability] '99.9%' is not of type 'number'
    → Semantic: sla.max_latency_ms: must be an integer

✗ 1/3 contract(s) failed validation
```

---

## Node.js Validator (`validate-contract.js`) — deprecated

> **Deprecated.** This standalone script is kept for backward compatibility and now
> delegates to `lib/validator.js`. Use `aof validate` (via `bin/aof.js`) instead.

**Requirements:** Node.js 18+

### Install

```bash
cd tools
npm install
```

### Usage

```bash
# Validate a single file
node validate-contract.js examples/support-agent.yaml

# Validate multiple files
node validate-contract.js examples/*.yaml

# Verbose output
node validate-contract.js --verbose examples/support-agent.yaml

# Show help
node validate-contract.js --help

# Via npm script
npm run validate -- examples/support-agent.yaml
npm test   # Validates all examples
```

### Example Output

```
✓ support-agent.yaml
✗ my-broken-contract.yaml
    → Schema: [/agent/type] must be equal to one of the allowed values
    → Semantic: sla.availability: '99.9%' must be a number (e.g., 99.9), not a string

✗ 1/2 contract(s) failed validation
```

---

## What Gets Validated

### JSON Schema Checks

- `apiVersion` must be `aof/v1`
- `kind` must be `AgentOwnershipContract`
- All required top-level sections present: `metadata`, `agent`, `purpose`, `ownership`, `authority`, `data`, `incident_response`, `governance`, `lifecycle`, `compliance`, `risk`, `signoff`, `dependencies`, `sla`
- `metadata.name` and `agent.id` match pattern `^[a-z0-9][a-z0-9-]*[a-z0-9]$`
- `metadata.version` matches semver pattern `^\d+\.\d+\.\d+$`
- `metadata.created` and `metadata.updated` are valid dates
- `agent.type` is one of: `autonomous`, `hybrid`, `advisory`
- `agent.name` has minimum 5 characters
- `agent.description` has minimum 50 characters
- `ownership.escalation_path` has at least 1 entry
- `authority.autonomous_decisions` has at least 1 entry
- `governance.review_cadence` is one of: `weekly`, `monthly`, `quarterly`, `annually`
- `governance.approval_required_for` has at least 1 entry
- `lifecycle.status` is one of: `active`, `conditional`, `pilot`, `paused`, `retired`
- `compliance.frameworks` has at least 1 entry
- `compliance.data_classification` is one of: `public`, `internal`, `restricted`, `highly-restricted`
- `compliance.pii_handling` has minimum 20 characters
- `compliance.retention_policy` has minimum 20 characters
- `risk.risk_tier` is one of: `low`, `medium`, `high`, `critical`
- `risk.blast_radius` has minimum 50 characters
- `sla.availability` is a number (not a string)
- `sla.max_latency_ms` is a positive integer

### Semantic Checks (beyond JSON Schema)

- `sla.availability` is between 0 and 100
- `sla.max_latency_ms` is >= 1
- `ownership.escalation_path` levels are sequential starting at 1
- `risk.kill_switch_owner` is a valid email address (if present)
- All escalation path email addresses are valid

---

## Common Validation Errors and Fixes

| Error | Fix |
|-------|-----|
| `sla.availability: '99.9%' is not of type 'number'` | Change `availability: "99.9%"` to `availability: 99.9` |
| `agent.type: must be equal to one of the allowed values` | Use `autonomous`, `hybrid`, or `advisory` |
| `compliance.data_classification: must be equal to one of allowed values` | Use `public`, `internal`, `restricted`, or `highly-restricted` |
| `lifecycle.status: must be equal to one of the allowed values` | Use `active`, `conditional`, `pilot`, `paused`, or `retired` |
| `escalation_path levels not sequential` | Ensure levels are 1, 2, 3, ... with no gaps or duplicates |
| `risk.kill_switch_owner is not a valid email` | Use a real individual email, not a team alias |
| `agent.description: must be >= 50 chars` | Write a fuller description (at least 50 characters) |
| `risk.blast_radius: must be >= 50 chars` | Write a more specific blast radius narrative |
| `YAML parse error: unhashable key` | Keys must not use `[bracket]` syntax — use quoted strings instead |

---

## CI/CD Integration

### GitHub Actions (quick snippet)

```yaml
- name: Validate AOF contracts
  run: |
    pip install ./tools
    aof validate examples
```

Or use the composite action directly:

```yaml
- uses: ajwork-art/agent-ownership-framework@v1
  with:
    contracts: examples
    strict: "true"
```

See [ci-cd/github-actions-validate.yml](../ci-cd/github-actions-validate.yml) for the full workflow.

### Pre-commit hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
changed_yamls=$(git diff --cached --name-only --diff-filter=ACM | grep ".*\.yaml")
if [ -n "$changed_yamls" ]; then
    aof validate $changed_yamls
    if [ $? -ne 0 ]; then
        echo "Contract validation failed. Fix errors before committing."
        exit 1
    fi
fi
```

Make executable: `chmod +x .git/hooks/pre-commit`
