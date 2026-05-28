# Troubleshooting Guide

Common issues when working with AOF contracts and how to resolve them.

---

## Schema Validation Errors

### sla.availability is not a number

**Error:**
```
Schema: [/sla/availability] must be number
```

**Bad:**
```yaml
sla:
  availability: "99.9%"   # String — INVALID
```

**Good:**
```yaml
sla:
  availability: 99.9      # Number — VALID
```

**Why:** `sla.availability` is a numeric percentage (0-100), not a formatted string.

---

### agent.type is not a valid value

**Error:**
```
Schema: [/agent/type] must be equal to one of the allowed values
```

**Bad:**
```yaml
agent:
  type: assistant    # Not a valid enum value
  type: pipeline     # Not a valid enum value
  type: agentic      # Not a valid enum value
```

**Good:**
```yaml
agent:
  type: autonomous   # Valid
  type: hybrid       # Valid
  type: advisory     # Valid
```

---

### compliance.data_classification is not a valid value

**Error:**
```
Schema: [/compliance/data_classification] must be equal to one of the allowed values
```

**Valid values:** `public`, `internal`, `restricted`, `highly-restricted`

**Bad:**
```yaml
compliance:
  data_classification: confidential     # Not valid
  data_classification: sensitive        # Not valid
  data_classification: "Restricted"     # Wrong case
```

**Good:**
```yaml
compliance:
  data_classification: restricted       # Lowercase, hyphenated for two-word values
```

---

### lifecycle.status is not valid

**Valid values:** `active`, `conditional`, `pilot`, `paused`, `retired`

**Bad:**
```yaml
lifecycle:
  status: production   # Not valid
  status: deprecated   # Not valid (use paused + retirement_date)
  status: inactive     # Not valid
```

---

### Required field missing

**Error:**
```
Schema: [(root)] must have required property 'accountability'
```

All of these top-level fields are required: `apiVersion`, `kind`, `metadata`, `agent`, `ownership`, `authority`, `accountability`, `governance`, `lifecycle`, `compliance`, `risk`, `dependencies`, `sla`

Do not omit any section, even if the agent has minimal governance needs. For low-risk agents, fill in minimal values (e.g., `dependencies: {}` if there are no external dependencies).

---

### agent.description too short

**Error:**
```
Schema: [/agent/description] must NOT have fewer than 50 characters
```

The description must be at least 50 characters. Write a real description of what the agent does and what it does not do.

---

### escalation levels not sequential

**Error:**
```
Semantic: ownership.escalation_path: levels [1, 3] are not sequential starting at 1 — expected [1, 2]
```

**Bad:**
```yaml
escalation_path:
  - level: 1
    name: Alice Smith
    email: alice@example.com
    role: Director
  - level: 3           # Gap! Level 2 is missing
    name: Bob Jones
    email: bob@example.com
    role: VP
```

**Good:**
```yaml
escalation_path:
  - level: 1
    name: Alice Smith
    email: alice@example.com
    role: Director
  - level: 2           # Sequential
    name: Bob Jones
    email: bob@example.com
    role: VP
```

---

### Invalid email format

**Error:**
```
Semantic: accountability.incident_contact: 'not-an-email' is not a valid email address
```

All email fields must be valid email addresses: `name@domain.com`

**Bad:**
```yaml
accountability:
  incident_contact: "the payments team"    # Not an email
  incident_contact: "payments"             # Not an email
```

**Good:**
```yaml
accountability:
  incident_contact: payments-oncall@example.com
```

---

## Ownership Assignment Challenges

### "We have no single owner — it's a shared agent"

**Problem:** Multiple teams use the agent and all resist being the primary owner.

**Resolution:** Primary ownership follows the business decision, not the infrastructure. Ask: if this agent causes harm to a customer or triggers a regulatory audit, who is the executive sponsor who answers for it? That person's team owns the agent. The engineering team maintaining the infrastructure may be listed as a secondary owner.

---

### "The original owner left the company"

**Problem:** The contract lists an employee who no longer works there.

**Resolution:** Update the contract immediately. This is a governance failure — contracts must be updated within 30 days of any ownership change. The new owner should be identified through the escalation path. If no one in the escalation path is current, escalate to the change control board.

---

### "The owner doesn't know enough about the agent to own it"

**Problem:** The business owner nominated as primary owner does not understand the technical details.

**Resolution:** Technical ownership and business ownership are different things. The primary owner is the business stakeholder who owns the decisions the agent makes. They do not need to understand the architecture. They need to understand the business impact and be reachable when the agent causes harm. Technical details belong in the `dependencies` section and the runbook.

---

## Governance Board Setup

### "We don't have a change control board"

**Problem:** No formal governance body exists for AI agents.

**Resolution:** The `change_control_board` field can reference an existing body (IT governance committee, risk committee, architecture review board) rather than creating a new one. For low-risk agents, a team lead group is sufficient. What matters is that a named group has the authority to approve changes — and that they know they have that authority.

---

### "The review cadence seems too frequent for our team"

**Problem:** Quarterly review feels like overhead for a stable, low-risk agent.

**Resolution:** Use `annually` for `risk_tier: low` agents. Reserve `quarterly` for medium and above. The cadence should match the risk — a fraud detection agent touching millions of transactions needs quarterly review; an internal wiki summarization tool does not.

---

## Incident Response Workflow Setup

### "We don't have PagerDuty / OpsGenie"

**Problem:** No formal on-call system exists.

**Resolution:** `on_call_rotation` is optional. Use `accountability.incident_contact` with a real email that is actively monitored. Even a team Slack channel email alias is better than nothing. What matters is that the `incident_contact` gets alerted when something goes wrong — whatever your mechanism is.

---

### "The runbook doesn't exist yet"

**Problem:** `runbook_url` points to a non-existent document.

**Resolution:** Do not leave `runbook_url` blank or pointing to a placeholder. Write the runbook first, then deploy the agent. A runbook can be as simple as: what to do when the agent is down, how to restart it, how to engage the kill switch. Three paragraphs in Confluence is enough to start.

---

## Contract Versioning

### When to increment which version number

| Change Type | Version Increment |
|------------|------------------|
| Typo fix, date update, label change | Patch (1.0.0 → 1.0.1) |
| New optional field added | Patch (1.0.0 → 1.0.1) |
| Ownership change | Minor (1.0.0 → 1.1.0) |
| Authority scope change | Minor (1.0.0 → 1.1.0) |
| Risk tier change | Minor (1.0.0 → 1.1.0) |
| Agent restructured / major scope change | Major (1.0.0 → 2.0.0) |
| Agent replaced by new agent | Retire this contract, create a new one |

---

## Migration from No Contracts to AOF

### Step-by-step for existing agents

**Week 1: Inventory**
Run a discovery exercise. List every AI agent currently in production. Include LLM-based tools, ML models making decisions, automation scripts with significant authority, and vendor AI systems your company has configured.

**Week 2-3: Assign draft ownership**
For each agent, identify who is most accountable for its business decisions. Create draft contracts using the template. Focus on getting `ownership`, `agent`, and `risk` sections filled in first.

**Week 4: Validate drafts**
Run `python tools/validate-contract.py contracts/*.yaml` on all drafts. Fix validation errors. Have primary owners review their contracts.

**Week 5: Fill compliance and governance**
Work with legal and compliance to complete `compliance.frameworks`, `compliance.pii_handling`, and `compliance.retention_policy`. Identify the change control board.

**Week 6: Sign-off and commit**
Primary owners review and approve contracts via PR. Merge to main. From this point, any change to an agent requires a contract update.

**Week 7+: Enforce**
Add CI/CD validation to reject contract updates that fail schema validation. Add contract review to the quarterly governance calendar.

### What to do with agents that cannot be governed

Some agents will have no identifiable owner, no clear authority scope, and no one willing to sign off. **These agents should be paused or retired.** An agent that cannot be governed should not be in production. The discovery process often reveals shadow AI — agents deployed without organizational awareness. These are the highest-risk agents precisely because no one owns them.
