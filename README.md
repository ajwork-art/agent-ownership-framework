# AI Agent Governance Contract
## Open Standard for Production AI Agent Ownership and Release

Developed by Anitha Jagadeesh

Published under the MIT License.

---

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/ajwork-art/agent-ownership-framework/releases)
[![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> **An agent is a product with delegated authority.** Treat it like one.

A production-grade, open-source framework for defining, documenting, and formalizing ownership of AI agents in enterprise environments. Inspired by the data contract movement and the author's experience governing production AI systems in enterprise environments.

---

## Scope

This repository is a governance standard and deployment-time contract validation layer.

It covers:
- Agent ownership contract schema
- Deployment readiness contract validation
- Eight governance pre-deployment checks
- CI/CD deployment gates

It does NOT cover:
- Runtime policy enforcement at inference time
- Runtime action interception or execution-time modification

Runtime enforcement is a separate architectural concern not covered by this repository.

---

## What's In This Repository

- `schema/` — Agent ownership contract schema
- `tools/` — Contract completeness validation tooling
- `examples/` — Example contracts by use case
- `ci-cd/` — CI/CD deployment check configurations
- `templates/` — Contract templates and implementation guides
- `docs/` — Implementation documentation

---

## Why This Exists

Enterprise AI deployments have a governance gap.

Teams build agents that query production databases, send emails, approve transactions, and modify customer records — but they cannot answer basic questions about who owns the agent, who approved its authority, what happens when it fails, and who gets paged at 2 AM.

This is not a tooling problem. It is an ownership problem.

The Agent Ownership Framework (AOF) closes that gap with machine-readable contracts that define — in a structured, version-controlled, validated format — exactly who owns each agent, what it is authorized to do, and how it is governed.

**Before deploying any agent, your team should be able to answer these eight questions:**

1. **Who owns this agent?** — A named human, not a team or a system
2. **What is it authorized to do?** — Specific actions, not "whatever the task requires"
3. **What data can it access?** — Classifications, retention policies, PII handling
4. **What happens when it fails?** — Incident contacts, runbooks, escalation paths
5. **Who reviews it and how often?** — Named reviewers, scheduled cadences
6. **What compliance frameworks apply?** — SOX, GLBA, PCI-DSS, GDPR, and others
7. **What is the blast radius if it malfunctions?** — Worst-case impact, documented
8. **How is it retired?** — Deprecation criteria, replacement agent, retirement date

If you cannot answer all eight, you are not ready to deploy.

---

## Quick Start

**Step 1: Copy the template**

```bash
cp templates/contract-template.yaml my-agent-contract.yaml
```

**Step 2: Fill in required fields**

```yaml
apiVersion: aof/v1
kind: AgentOwnershipContract

metadata:
  name: payment-processing-agent
  version: 1.0.0
  created: "2026-01-15"
  updated: "2026-01-15"

agent:
  id: payment-processing-agent
  name: Payment Processing Agent
  description: >
    Processes payment transactions for the checkout pipeline. Validates payment
    methods, applies fraud screening, and routes approved transactions to the
    payment gateway. Does not store raw card data.
  type: hybrid
  domain: financial-services

ownership:
  primary_owner:
    name: Jane Smith
    email: jane.smith@company.com
    team: Payments Platform
    org: Engineering
```

**Step 3: Fill in authority, accountability, governance, compliance, risk, and SLA sections**

See [examples/fraud-detection-agent.yaml](examples/fraud-detection-agent.yaml) for a fully completed contract across all sections, or [schema/v1/agent-ownership-contract.example.yaml](schema/v1/agent-ownership-contract.example.yaml) for a field-by-field annotated reference. The [templates/contract-checklist.md](templates/contract-checklist.md) will tell you if you have missed anything.

**Step 4: Validate your contract**

```bash
# Python
cd tools && pip install -r requirements.txt
python validate-contract.py ../my-agent-contract.yaml

# Node.js
cd tools && npm install
node validate-contract.js ../my-agent-contract.yaml
```

**Step 5: Commit and enforce**

```bash
git add my-agent-contract.yaml
git commit -m "feat: add agent ownership contract for payment processing agent"
```

Add the [CI/CD workflow](.github/workflows/validate-contracts.yml) to validate all contracts on every pull request.

---

## Why YAML?

YAML is human-readable, version-controllable, commentable, and supported by every CI/CD system. Combined with Git, it gives you an immutable audit trail — who created the contract, who changed it, when, and why. For tamper-resistance in CI/CD: store a SHA-256 hash of the contract alongside it; the validator checks the hash before accepting the contract. JSON is fully equivalent for tooling; the schema ships in JSON for machine consumption. TOML and HCL are viable alternatives but lack the comment support that makes contracts readable to non-engineers.

---

## Why not Open Policy Agent?

OPA enforces policy at runtime — it decides whether a specific request is allowed at the moment it happens. AOF defines governance at design time — it answers who owns an agent, what it is authorized to do, and who is accountable before the agent is deployed. These solve different problems and complement each other: AOF defines the contract, and a separate runtime policy layer may choose to enforce those boundaries.

---

## Directory Structure

```
agent-ownership-framework/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── CONTRIBUTING.md                    # Contribution guidelines
│
├── schema/
│   ├── README.md                      # Schema documentation
│   └── v1/
│       ├── agent-ownership-contract.schema.json   # JSON Schema (draft-07)
│       └── agent-ownership-contract.example.yaml  # Annotated reference example
│
├── examples/
│   ├── README.md                      # Examples index
│   ├── support-agent.yaml             # Customer support (autonomous, medium risk)
│   ├── operations-agent.yaml          # Operations workflow (hybrid, medium risk)
│   ├── fraud-detection-agent.yaml     # Fraud detection (autonomous, critical risk)
│   ├── risk-analysis-agent.yaml       # Risk analysis (advisory, high risk)
│   └── internal-tool-agent.yaml       # Internal tooling (autonomous, low risk)
│
├── tools/
│   ├── README.md                      # Tool documentation
│   ├── validate-contract.py           # Python validator
│   ├── validate-contract.js           # Node.js validator
│   ├── requirements.txt               # Python dependencies
│   └── package.json                   # Node.js dependencies
│
├── docs/
│   ├── FRAMEWORK.md                   # Framework concepts and walkthrough
│   ├── PRINCIPLES.md                  # Four core principles
│   ├── SCHEMA.md                      # Complete field reference
│   ├── INTEGRATION.md                 # Runtime and CI/CD integration
│   ├── COMPLIANCE.md                  # Regulatory framework mappings
│   ├── TROUBLESHOOTING.md             # Common issues and solutions
│   └── FAQ.md                         # Frequently asked questions
│
├── templates/
│   ├── contract-template.yaml         # Blank contract with comments
│   ├── contract-checklist.md          # Pre-launch verification checklist
│   ├── implementation-guide.md        # Week-by-week enterprise roadmap
│   └── schema-fields-explained.md     # Non-technical field explanations
│
└── ci-cd/
    ├── README.md                      # CI/CD integration overview
    ├── github-actions-validate.yml    # GitHub Actions workflow
    ├── gitlab-ci.yml                  # GitLab CI equivalent
    └── terraform-validate.tf          # Terraform integration
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/FRAMEWORK.md](docs/FRAMEWORK.md) | Framework concepts, the delegation problem, ownership failure patterns, agent lifecycle |
| [docs/PRINCIPLES.md](docs/PRINCIPLES.md) | The four core AOF principles with schema field mappings |
| [docs/SCHEMA.md](docs/SCHEMA.md) | Complete field-by-field reference for every schema section |
| [docs/INTEGRATION.md](docs/INTEGRATION.md) | CI/CD enforcement, GitHub Actions, GitLab, Terraform, pre-commit hooks |
| [docs/COMPLIANCE.md](docs/COMPLIANCE.md) | Regulatory mappings for SOX, GLBA, PCI-DSS, GDPR, HIPAA, EU AI Act |
| [docs/FAQ.md](docs/FAQ.md) | Common questions and answers |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common validation errors and how to fix them |
| [templates/implementation-guide.md](templates/implementation-guide.md) | Week-by-week enterprise adoption roadmap |
| [templates/contract-checklist.md](templates/contract-checklist.md) | Pre-launch checklist — verify all eight governance questions before deploying |
| [tools/README.md](tools/README.md) | Validator usage, all flags, example output, and common error fixes |

---

## Examples

Five production-realistic examples covering the most common enterprise agent patterns:

| Example | Domain | Risk Tier | Type | Key Compliance |
|---------|--------|-----------|------|----------------|
| [support-agent.yaml](examples/support-agent.yaml) | Customer Service | Medium | Autonomous | SOX, GLBA |
| [operations-agent.yaml](examples/operations-agent.yaml) | Operations | Medium | Hybrid | SOX |
| [fraud-detection-agent.yaml](examples/fraud-detection-agent.yaml) | Financial Services | Critical | Autonomous | PCI-DSS, BSA-AML, SOX, GLBA |
| [risk-analysis-agent.yaml](examples/risk-analysis-agent.yaml) | Risk Management | High | Advisory | GDPR, SOX, FCRA, GLBA |
| [internal-tool-agent.yaml](examples/internal-tool-agent.yaml) | Internal Tooling | Low | Autonomous | Internal policy only |

---

## Validation Tools

| Tool | Language | Install |
|------|----------|---------|
| [validate-contract.py](tools/validate-contract.py) | Python 3.8+ | `pip install -r tools/requirements.txt` |
| [validate-contract.js](tools/validate-contract.js) | Node.js 18+ | `npm install` in `tools/` |

Both tools validate against the JSON Schema, check email formats, verify SLA ranges, and confirm escalation path sequencing.

---

## Related Resources

This repository is part of the AI Agent Governance Framework:

- **Article:** [An Agent Is a Product With Delegated Authority](https://enterprisedataairealities.substack.com/p/an-agent-is-a-product-with-delegated) — Enterprise Data AI Realities on Substack

- **Agent Boundary Evaluator:** [innocorestrategy.com/agent-boundary-assessment](https://innocorestrategy.com/agent-boundary-assessment/) — AI Agent Governance Standard and assessment tool

- **This repository:** Deployment-time contract validation layer

---

## Contributing

Contributions are welcome — especially new examples, compliance mappings, and tool integrations.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- How to submit a new agent contract example
- What makes a good example (the hard decisions, not the easy ones)
- Code of conduct and PR process

---

## Citation

If you reference AOF in a paper, blog, or presentation:

```
Jagadeesh, Anitha. Agent Ownership Framework (AOF), v1.0.0. 2026.
https://github.com/ajwork-art/agent-ownership-framework
Enterprise Data AI Realities — Substack.
```

---

## Attribution

If you use, adapt, or build on this standard, please preserve the original copyright and license notice.

> "AI Agent Governance Contract — Anitha Jagadeesh"

If you reference this work publicly, please link back to this repository.

---

## License

MIT License — Copyright 2026 Anitha Jagadeesh

See [LICENSE](LICENSE) for full terms.

---

*Built by [Anitha Jagadeesh](https://substack.com/@anithaenterprisedataai).*
