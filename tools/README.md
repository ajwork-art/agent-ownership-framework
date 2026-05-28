# Tools

Validation tools for AOF v1 agent ownership contracts. Both tools validate against the JSON Schema and perform additional semantic checks.

---

## Python Validator

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
    → Semantic: [accountability.incident_contact] 'not-an-email' is not a valid email address

✗ 1/3 contract(s) failed validation
```

---

## Node.js Validator

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
- All required top-level sections present: `metadata`, `agent`, `ownership`, `authority`, `accountability`, `governance`, `lifecycle`, `compliance`, `risk`, `dependencies`, `sla`
- `metadata.name` and `agent.id` match pattern `^[a-z0-9][a-z0-9-]*[a-z0-9]$`
- `metadata.version` matches semver pattern `^\d+\.\d+\.\d+$`
- `metadata.created` and `metadata.updated` are valid dates
- `agent.type` is one of: `autonomous`, `hybrid`, `advisory`
- `agent.name` has minimum 5 characters
- `agent.description` has minimum 50 characters
- `ownership.escalation_path` has at least 1 entry
- `authority.scope_limits` has at least 1 entry
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
- `accountability.incident_contact` is a valid email address
- `risk.kill_switch_owner` is a valid email address (if present)
- `ownership.primary_owner.email` is a valid email address
- All escalation path email addresses are valid

---

## Common Validation Errors and Fixes

| Error | Fix |
|-------|-----|
| `sla.availability: '99.9%' is not of type 'number'` | Change `availability: "99.9%"` to `availability: 99.9` |
| `agent.type: must be equal to one of the allowed values` | Use `autonomous`, `hybrid`, or `advisory` (not `assistant` or `pipeline`) |
| `compliance.data_classification: must be equal to one of allowed values` | Use `public`, `internal`, `restricted`, or `highly-restricted` |
| `lifecycle.status: must be equal to one of the allowed values` | Use `active`, `conditional`, `pilot`, `paused`, or `retired` |
| `escalation_path levels not sequential` | Ensure levels are 1, 2, 3, ... with no gaps or duplicates |
| `incident_contact is not a valid email` | Use a valid email like `team-alerts@company.com` |
| `agent.description: must be >= 50 chars` | Write a fuller description (at least 50 characters) |
| `risk.blast_radius: must be >= 50 chars` | Write a more specific blast radius narrative |
| `Required field missing: [field]` | Add the missing required section to your contract |

---

## CI/CD Integration

### GitHub Actions (quick snippet)

```yaml
- name: Validate AOF contracts
  run: |
    pip install pyyaml jsonschema
    python tools/validate-contract.py examples/*.yaml
```

See [ci-cd/github-actions-validate.yml](../ci-cd/github-actions-validate.yml) for the full workflow.

### Pre-commit hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
changed_yamls=$(git diff --cached --name-only --diff-filter=ACM | grep "examples/.*\.yaml")
if [ -n "$changed_yamls" ]; then
    python tools/validate-contract.py $changed_yamls
    if [ $? -ne 0 ]; then
        echo "Contract validation failed. Fix errors before committing."
        exit 1
    fi
fi
```

Make executable: `chmod +x .git/hooks/pre-commit`
