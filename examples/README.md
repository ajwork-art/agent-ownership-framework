# Examples

Five production-realistic AOF v1 contract examples covering common enterprise agent patterns. Use these as starting points for your own contracts.

---

## Examples Index

| File | Domain | Risk Tier | Type | Key Compliance |
|------|--------|-----------|------|----------------|
| [support-agent.yaml](support-agent.yaml) | Customer Service | Medium | Autonomous | SOX, GLBA |
| [operations-agent.yaml](operations-agent.yaml) | Operations | Medium | Hybrid | SOX |
| [fraud-detection-agent.yaml](fraud-detection-agent.yaml) | Financial Services | Critical | Autonomous | PCI-DSS, BSA-AML, SOX, GLBA |
| [risk-analysis-agent.yaml](risk-analysis-agent.yaml) | Risk Management | High | Advisory | GDPR, SOX, FCRA, GLBA |
| [internal-tool-agent.yaml](internal-tool-agent.yaml) | Internal Tooling | Low | Autonomous | Internal policy |

---

## When to Use Each Example

### support-agent.yaml — Customer Support (Medium Risk, Autonomous)

Use this as a starting point when:
- Your agent interacts directly with customers
- It has bounded financial authority (refunds, credits, adjustments)
- It requires human escalation above a threshold
- The domain involves PII (names, account numbers, transaction history)

Key patterns: bounded authority with dollar limits, two-level escalation, quarterly review, PII masking in logs.

---

### operations-agent.yaml — Internal Workflow (Medium Risk, Hybrid)

Use this as a starting point when:
- Your agent automates internal business workflows
- It initiates actions but cannot approve or commit financial decisions
- It integrates with multiple internal systems (ERP, vendor portals)
- Rate limiting on external API calls is needed

Key patterns: hybrid type with initiation-but-not-approval separation, SOX audit trail for financial workflows, rate limits in scope_limits.

---

### fraud-detection-agent.yaml — High-Volume Autonomous (Critical Risk)

Use this as a starting point when:
- Your agent runs fully autonomously at high throughput
- Latency requirements make HITL operationally impossible
- The agent is "scoring only" — downstream systems make the actual decisions
- Multiple regulatory frameworks apply (PCI-DSS, AML, SOX)
- The blast radius is existential at platform scale

Key patterns: three-level escalation, scoring-only authority with no block/approve capability, four-nines availability, highly-restricted data classification, HITL false with explicit rationale.

---

### risk-analysis-agent.yaml — Advisory (High Risk)

Use this as a starting point when:
- Your agent produces recommendations that influence regulated decisions
- The agent type is advisory — humans always decide
- FCRA, GDPR, or similar regulations apply to the data being analyzed
- Read-only access is the core authority boundary

Key patterns: advisory type with read-only authority, FCRA explainability requirements, conflicting retention obligations (GDPR vs SOX), high risk despite no direct decision authority.

---

### internal-tool-agent.yaml — Internal Tooling (Low Risk)

Use this as a starting point when:
- Your agent is internal-only with no customer data access
- The blast radius is limited to productivity loss, no financial or regulatory impact
- Annual review is sufficient given low risk and stable scope
- You need to demonstrate that even low-risk agents get contracts

Key patterns: minimal governance overhead, annual review cadence, 95% availability SLA, no HITL required, simple two-level escalation.

---

## How to Copy and Customize

**Step 1: Copy the closest example**

```bash
cp examples/support-agent.yaml my-new-agent-contract.yaml
```

**Step 2: Update required fields at minimum**

```yaml
metadata:
  name: your-agent-name          # Must be unique kebab-case slug
  version: 1.0.0
  created: "2026-XX-XX"          # Today's date
  updated: "2026-XX-XX"          # Today's date

agent:
  id: your-agent-name            # Matches metadata.name
  name: Your Agent Display Name
  description: >
    [50+ character description of what this agent does and what it does NOT do]
  type: autonomous                # or hybrid, advisory
  domain: your-domain

ownership:
  primary_owner:
    name: Actual Person Name      # A real named human, not a team
    email: real.email@yourcompany.com
    team: Your Team
    org: Your Org
```

**Step 3: Review and fill in all required sections**

All of these sections are required — do not leave any blank:
- `authority` — be specific about scope_limits
- `accountability` — use a real incident_contact email
- `governance` — name a real change_control_board
- `lifecycle` — set the correct status
- `compliance` — list every applicable framework
- `risk` — write an honest blast_radius narrative
- `dependencies` — list all models, services, and data sources
- `sla` — use numbers from your actual SLO targets

**Step 4: Validate**

```bash
python tools/validate-contract.py my-new-agent-contract.yaml
```

**Step 5: Commit to version control**

```bash
git add my-new-agent-contract.yaml
git commit -m "feat: add agent ownership contract for [agent name]"
```

---

## Validation

Validate any contract against the JSON Schema:

```bash
# Single file
python tools/validate-contract.py examples/support-agent.yaml

# All examples
python tools/validate-contract.py examples/*.yaml

# With verbose output
python tools/validate-contract.py --verbose examples/fraud-detection-agent.yaml

# Machine-readable JSON output
python tools/validate-contract.py --output json examples/support-agent.yaml
```

Or with Node.js:

```bash
node tools/validate-contract.js examples/support-agent.yaml
```

---

## What You Must Update (at minimum)

When copying an example, always update:

| Field | Why |
|-------|-----|
| `metadata.name` | Must be unique to your agent |
| `metadata.created` / `metadata.updated` | Use actual dates |
| `agent.id` | Must match metadata.name |
| `agent.description` | Describe your actual agent |
| `ownership.primary_owner` | A real named person at your organization |
| `ownership.escalation_path` | Real escalation contacts |
| `accountability.incident_contact` | A real monitored email address |
| `governance.change_control_board` | A real governance body |
| `risk.blast_radius` | Honest assessment of YOUR agent's impact |
| `risk.kill_switch_owner` | A real named person who can act immediately |

Never submit a contract with placeholder values or fictional names for real governance decisions.

---

## Contributing Examples

If you have built an agent contract that would help others, contributions are welcome. See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines. The most useful examples are:

- From domains not yet covered (healthcare, insurance, logistics, legal)
- With unusual governance patterns worth documenting
- With compliance frameworks not yet represented

All examples must pass schema validation before submission.
