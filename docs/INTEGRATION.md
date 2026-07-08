# Integration Guide

How to integrate AOF contracts into your development workflow and CI/CD pipeline.

---

## Validating Before Deployment

Run validation as part of your deployment pipeline:

```bash
# Install dependencies
pip install pyyaml jsonschema

# Validate all contracts before deploying
python tools/validate-contract.py contracts/*.yaml

# Exit code 0 = all valid, exit code 1 = failures
if [ $? -ne 0 ]; then
    echo "Contract validation failed. Deployment blocked."
    exit 1
fi
```

---

## GitHub Actions Integration

Full workflow for validating contracts on every pull request that modifies contracts or the schema.

```yaml
# .github/workflows/validate-contracts.yml
name: Validate AOF Contracts

on:
  push:
    paths:
      - "examples/**"
      - "schema/**"
  pull_request:
    paths:
      - "examples/**"
      - "schema/**"

jobs:
  validate:
    name: Validate Contracts
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install pyyaml jsonschema

      - name: Validate all example contracts
        run: python tools/validate-contract.py examples/*.yaml

      - name: Report results
        if: failure()
        run: |
          echo "One or more contracts failed validation."
          echo "Run: python tools/validate-contract.py examples/*.yaml --verbose"
          echo "See docs/SCHEMA.md for field reference."
```

See [.github/workflows/ci.yml](../.github/workflows/ci.yml) for the full version.

---

## GitLab CI Integration

```yaml
# .gitlab-ci.yml (excerpt)
validate-contracts:
  stage: validate
  image: python:3.11-slim
  script:
    - pip install pyyaml jsonschema
    - python tools/validate-contract.py examples/*.yaml
  rules:
    - changes:
        - examples/**/*.yaml
        - schema/**
```

---

## Terraform Integration

Enforce contract validation as part of infrastructure provisioning:

```hcl
# ci-cd/terraform-validate.tf
variable "contract_path" {
  description = "Path to the AOF contract YAML file"
  type        = string
}

variable "python_path" {
  description = "Path to the Python interpreter"
  type        = string
  default     = "python3"
}

resource "null_resource" "validate_aof_contract" {
  triggers = {
    contract_hash = filemd5(var.contract_path)
  }

  provisioner "local-exec" {
    command = "${var.python_path} tools/validate-contract.py ${var.contract_path}"
  }
}
```

Usage:

```hcl
module "agent_contract_validation" {
  source        = "./ci-cd"
  contract_path = "contracts/payment-agent.yaml"
}
```

---

## Contract Registry Pattern

For organizations with many agents, implement a contract registry that loads and indexes contracts at startup:

```python
import os
import glob
import yaml
import json
import jsonschema
from typing import Dict, Optional

class ContractRegistry:
    """
    Loads and indexes all AOF contracts in a directory.
    Use at application startup to make contracts queryable by agent ID.
    """

    def __init__(self, contracts_dir: str, schema_path: str):
        with open(schema_path) as f:
            self.schema = json.load(f)
        self.contracts: Dict[str, dict] = {}
        self._load_all(contracts_dir)

    def _load_all(self, directory: str):
        pattern = os.path.join(directory, "**/*.yaml")
        for filepath in glob.glob(pattern, recursive=True):
            try:
                with open(filepath) as f:
                    contract = yaml.safe_load(f)
                jsonschema.validate(instance=contract, schema=self.schema)
                agent_id = contract["agent"]["id"]
                self.contracts[agent_id] = contract
            except Exception as e:
                print(f"WARNING: Failed to load contract {filepath}: {e}")

    def get(self, agent_id: str) -> Optional[dict]:
        """Get a contract by agent ID."""
        return self.contracts.get(agent_id)

    def list_by_risk_tier(self, tier: str) -> list:
        """List all agents with a given risk tier."""
        return [
            c for c in self.contracts.values()
            if c.get("risk", {}).get("risk_tier") == tier
        ]

    def list_overdue_reviews(self) -> list:
        """List contracts where next_review date has passed."""
        from datetime import date
        today = date.today().isoformat()
        overdue = []
        for c in self.contracts.values():
            next_review = c.get("governance", {}).get("next_review")
            if next_review and next_review < today:
                overdue.append(c)
        return overdue


# Usage
registry = ContractRegistry(
    contracts_dir="contracts/",
    schema_path="schema/v1/agent-ownership-contract.schema.json"
)

# Get a specific agent's contract
fraud_contract = registry.get("fraud-detection-agent")

# Audit: find all critical agents
critical_agents = registry.list_by_risk_tier("critical")

# Governance: find overdue reviews
overdue = registry.list_overdue_reviews()
for c in overdue:
    print(f"OVERDUE: {c['agent']['id']} — contact {c['ownership']['primary_owner']['email']}")
```

---

## Pre-commit Hook

Validate contracts automatically before every git commit:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Find YAML files in examples/ that are staged for commit
changed_yamls=$(git diff --cached --name-only --diff-filter=ACM | grep "examples/.*\.yaml")

if [ -n "$changed_yamls" ]; then
    echo "Validating AOF contracts..."
    python tools/validate-contract.py $changed_yamls

    if [ $? -ne 0 ]; then
        echo ""
        echo "Contract validation failed. Fix errors before committing."
        echo "Run: python tools/validate-contract.py --verbose <file>"
        exit 1
    fi

    echo "All contracts valid."
fi
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

---

## Optional: signature verification (`aof verify`)

Signing an AOF contract is **entirely optional**. AOF does not ship a PKI, does not
generate or store private keys, and does not require signatures to validate a
contract. `aof verify` is a defense-in-depth option for teams that want cryptographic
proof that a specific key holder approved a contract file. Signing happens **out of
band**; AOF only verifies.

### GPG (implemented)

```bash
# One-time: the signer creates/holds their own key (AOF never touches private keys)
gpg --full-generate-key

# Sign a contract, producing a detached signature next to it
gpg --armor --detach-sign my-agent.yaml        # -> my-agent.yaml.asc

# A verifier imports the signer's PUBLIC key, then verifies
gpg --import signer-public-key.asc
aof verify my-agent.yaml                        # finds my-agent.yaml.asc automatically
aof verify my-agent.yaml --signature path/to/detached.sig
```

`aof verify` exits `0` on a good signature and non-zero otherwise. Key distribution
and trust are the operator's responsibility.

### Sigstore / cosign (recipe — keyless, experimental)

[Sigstore](https://www.sigstore.dev/) `cosign` can sign a contract as a blob using
short-lived, identity-bound certificates (no long-lived private key to store). AOF
does not wrap cosign; use it directly and gate on its exit code:

```bash
# Sign (keyless — opens an OIDC identity flow; records to the transparency log)
COSIGN_EXPERIMENTAL=1 cosign sign-blob \
  --output-signature my-agent.yaml.sig \
  --output-certificate my-agent.yaml.pem \
  my-agent.yaml

# Verify — pin the expected signer identity and issuer
COSIGN_EXPERIMENTAL=1 cosign verify-blob \
  --certificate my-agent.yaml.pem \
  --signature my-agent.yaml.sig \
  --certificate-identity 'owner@your-org.com' \
  --certificate-oidc-issuer 'https://accounts.google.com' \
  my-agent.yaml
```

This recipe is documented but not yet wrapped by the `aof` CLI. As with GPG, it is
optional and orthogonal to schema validation.
