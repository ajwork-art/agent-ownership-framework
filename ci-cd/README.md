# CI/CD Integration

Validation workflows for enforcing AOF contracts in continuous integration and deployment pipelines.

---

## Overview

AOF validation should run automatically whenever a contract is modified. This prevents invalid contracts from being merged and ensures every agent in your repository has a valid, schema-compliant ownership contract.

**When to validate:**
- On every pull request that modifies files in `examples/` or `schema/`
- Before provisioning infrastructure for an agent (Terraform)
- As a pre-commit hook on developer machines
- As part of any deployment pipeline that references an agent contract

**What to do on failure:**
- Block the PR merge (CI/CD) or deployment (Terraform)
- Report which files failed and which fields are invalid
- Link to the troubleshooting guide
- Never allow a workaround that skips validation

---

## GitHub Actions

**File:** `github-actions-validate.yml`

This workflow triggers on pushes and pull requests that modify `examples/**` or `schema/**`.

**To use in your repository:**

1. Copy to `.github/workflows/validate-contracts.yml`
2. Ensure your repository has `examples/*.yaml` contracts
3. Open a PR modifying any example — the workflow runs automatically

```yaml
# Quick reference — full file at github-actions-validate.yml
on:
  push:
    paths: ["examples/**", "schema/**"]
  pull_request:
    paths: ["examples/**", "schema/**"]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install pyyaml jsonschema
      - run: python tools/validate-contract.py examples/*.yaml
```

See [.github/workflows/ci.yml](../.github/workflows/ci.yml) for the full workflow used in this repository.

---

## GitLab CI

**File:** `gitlab-ci.yml`

Equivalent GitLab CI configuration. Triggers only on changes to `examples/` or `schema/`.

**To use:**

1. Copy the `validate-aof-contracts` job into your existing `.gitlab-ci.yml`
2. Adjust the `rules.changes` paths if your contracts are in a different location

---

## Terraform

**File:** `terraform-validate.tf`

Runs the Python validator as a `null_resource` provisioner before creating infrastructure. Blocks `terraform apply` if the contract fails validation.

**To use:**

```hcl
module "contract_validation" {
  source        = "./ci-cd"
  contract_path = "contracts/my-agent-contract.yaml"
  python_path   = "python3"   # Optional, defaults to python3
}

# Make your agent infrastructure depend on contract validation
resource "aws_lambda_function" "my_agent" {
  depends_on = [module.contract_validation]
  # ... rest of your resource config
}
```

Variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `contract_path` | (required) | Path to the YAML contract file |
| `python_path` | `python3` | Path to Python interpreter |
| `validator_path` | `tools/validate-contract.py` | Path to the validator script |

---

## Common Failure Modes and Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| `must be number` on `sla.availability` | Used `"99.9%"` string format | Change to `99.9` (no quotes, no percent sign) |
| `must be equal to one of the allowed values` on `agent.type` | Used `assistant` or `pipeline` | Use `autonomous`, `hybrid`, or `advisory` |
| `Required field missing` | Omitted a required section | Add the missing section — all 13 top-level fields are required |
| `levels not sequential` | Escalation levels have a gap | Renumber levels 1, 2, 3... with no gaps |
| Validator not found | Wrong path to `validate-contract.py` | Run from repository root or adjust `validator_path` |

For more, see [docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md).
