# AOF Framework Guide

The Agent Ownership Framework (AOF) is a structured standard for defining ownership, authority, and accountability for production AI agents. This document explains why it exists, how it works, and how to apply it.

---

## What Is AOF?

AOF is a contract schema, a set of principles, and a validation toolchain for answering one question:

**Who is responsible for this agent, and what is it authorized to do?**

AOF defines a machine-readable YAML contract format (the AgentOwnershipContract) that any team can fill out before deploying an AI agent. The contract captures ownership, authority boundaries, compliance requirements, risk assessment, and governance cadence — in a structured format that can be version-controlled, reviewed, validated automatically, and enforced at runtime.

Inspired by the data contract movement and the author's experience governing production AI systems in enterprise environments — AOF applies contract-based governance to agents rather than data assets.

---

## The Delegation Problem

When you deploy an AI agent, you are not just deploying software. You are delegating authority.

An agent that can query databases, send emails, approve transactions, or modify customer records has been given decision-making power that previously required a human. That delegation is a consequential act — but most organizations treat it as a deployment detail, not a governance decision.

The result is a delegation gap: authority has been granted, but it has not been documented, bounded, reviewed, or owned.

This gap surfaces during incidents. When an agent misbehaves, the questions are immediate: Who owns this? Who approved its authority to do that? What is the escalation path? How do we shut it down? Where is the runbook?

Without an ownership contract, the answers are improvised. With one, they are declared.

---

## The Four Ownership Failure Patterns

In practice, agent ownership fails in four predictable ways:

### 1. No Owner

The agent was built by a project team that disbanded or moved on. There is no named human who is accountable. When it fails, no one knows who to call.

**Contract response:** `ownership.primary_owner` requires a named individual with a current email address. Not a team mailbox. Not a shared alias. A person.

### 2. Ownership Changed Without Transfer

The original owner left the company. The new team running the agent never formally took ownership. The contract (if one exists) still lists the previous owner.

**Contract response:** `metadata.updated` and `metadata.version` must change whenever ownership changes. The contract lives in version control, so ownership transfers are auditable events.

### 3. Diffused Ownership

Multiple teams claim partial ownership: the ML team owns the model, the product team owns the use case, the platform team owns the infrastructure. When something goes wrong, each team assumes another team is responsible.

**Contract response:** AOF requires exactly one `primary_owner`. Secondary owners are optional and supplementary. There is always a clear single point of accountability.

### 4. Technical Ownership Is Not Business Ownership

The engineering team that deployed the agent considers themselves the owner. But the business decisions the agent makes — refunds, risk flags, customer communications — belong to a business owner who has no idea an agent is making those decisions.

**Contract response:** The `ownership.primary_owner` should be the person who is accountable for the business decisions the agent makes — not just the person who runs the infrastructure. In many cases, this is a business or product leader, not an engineer.

---

## The Eight Ownership Questions

AOF is organized around eight questions that every deployed agent must be able to answer:

| # | Question | AOF Fields |
|---|----------|-----------|
| 1 | Who owns this agent? | `ownership.primary_owner` |
| 2 | What is it authorized to do? | `authority.scope_limits`, `authority.can_*` flags |
| 3 | What data can it access? | `compliance.data_classification`, `compliance.pii_handling` |
| 4 | What happens when it fails? | `accountability.incident_contact`, `accountability.runbook_url` |
| 5 | Who reviews it and how often? | `governance.review_cadence`, `governance.change_control_board` |
| 6 | What compliance frameworks apply? | `compliance.frameworks`, `compliance.audit_log_required` |
| 7 | What is the blast radius? | `risk.blast_radius`, `risk.risk_tier` |
| 8 | How is it retired? | `lifecycle.retirement_date`, `lifecycle.replacement_agent_id` |

If a team cannot answer all eight before deployment, the agent is not ready for production.

---

## The Eight Boundaries

Every AOF contract covers eight governance boundaries. Each boundary maps to one or more schema sections. The table below shows exactly which fields satisfy which boundary.

| Boundary | Schema Section | What it covers |
|----------|---------------|----------------|
| 1. Purpose | `purpose` | `business_purpose`, `success_metrics`, `out_of_scope` |
| 2. Ownership | `ownership` | `domain_owner`, `technical_owner`, `data_owner`, `risk_owner` |
| 3. Authority | `authority` | `autonomous_decisions`, `escalation_triggers`, `prohibited_actions`, `override_mechanism` |
| 4. Data | `data` | `permitted_sources`, `prohibited_sources`, `sensitive_data_handling` |
| 5. Evidence | `incident_response` | `investigation_scope`, log access, incident reconstruction |
| 6. Lifecycle | `lifecycle` + `governance` | review cadence, monitoring, retirement criteria |
| 7. Approval | `signoff` | named signatures, launch conditions |
| 8. Failure accountability | `incident_response` | investigator, communication owners, post-incident review |

**Boundary 1 — Purpose** declares the business case, measurable success criteria, and explicit out-of-scope behaviors. An agent that cannot answer "what is it for, and what is it explicitly not for?" should not go to production.

**Boundary 2 — Ownership** names a specific human for each accountability role. Domain owners accept business risk; technical owners accept build and runtime risk; data owners accept data compliance risk; risk owners accept regulatory exposure.

**Boundary 3 — Authority** declares the agent's decision-making envelope: what it can decide autonomously, what forces escalation, what it can never do, and who can stop it with a defined SLA.

**Boundary 4 — Data** is a whitelist. If a data source is not in `permitted_sources`, access is unauthorized. The `prohibited_sources` list makes common temptations explicit and detectable in audit logs.

**Boundary 5 — Evidence** ensures that when an incident occurs, there is a declared investigator, log access policy, and a minimum set of questions the investigation must answer. Without this, incident reconstruction is improvised.

**Boundary 6 — Lifecycle** tracks the agent from deployment through retirement. Agents without retirement criteria run forever, accumulate governance debt, and fail in ways no one anticipated.

**Boundary 7 — Approval** is the pre-launch gate. Named owners sign the contract before deployment. The signature is version-controlled — it is an auditable record that a specific person accepted accountability on a specific date.

**Boundary 8 — Failure Accountability** names who communicates with customers, stakeholders, and regulators when the agent fails. This must be declared before failure, not improvised during it.

---

## How Contracts Work

An AOF contract is:

- **Machine-readable** — YAML format validated against a JSON Schema
- **Version-controlled** — Lives in Git; every change is tracked
- **Validated automatically** — CI/CD pipeline rejects invalid contracts on every PR
- **Enforceable at runtime** — Applications can load the contract and use it to gate agent actions

A contract is not a README. It is a structured declaration with a schema, a validator, and tooling to enforce it. That is what separates AOF from documentation.

---

## Step-by-Step: Create Your First Contract

**Step 1: Start from a template**

```bash
cp templates/contract-template.yaml contracts/my-agent-contract.yaml
```

**Step 2: Fill in the agent section**

Be specific about what the agent does and — critically — what it does NOT do. The description is where you define scope.

**Step 3: Assign an owner**

Name a specific human, not a team. This person is accountable when the agent causes harm. If you cannot name someone willing to be accountable, the agent should not go to production.

**Step 4: Define authority boundaries**

Fill in the `authority` section honestly. Set `can_approve_actions: false` unless the agent genuinely has approval authority. The `scope_limits` list is the most important part — make it specific.

**Step 5: Fill in risk and compliance**

Write the `risk.blast_radius` narrative as if you are briefing a VP the day the agent fails. Be honest about the worst case.

**Step 6: Validate**

```bash
python tools/validate-contract.py contracts/my-agent-contract.yaml
```

**Step 7: Get sign-off**

Have the named primary owner review and approve the contract. Commit both the contract and the approval (via PR review) to version control.

**Step 8: Deploy with the contract**

Reference the contract in your deployment. At runtime, your application can load the contract to enforce authority limits.

---

## Contract Lifecycle

```
Create → Review → Sign-off → Deploy → Monitor → Quarterly Review → Update or Retire
```

**Create:** Draft the contract during the agent design phase, not after deployment.

**Review:** The named primary owner, a compliance representative, and a security representative review the contract before sign-off.

**Sign-off:** The primary owner and a change control board representative approve the contract. This approval is captured as a Git merge by the approving parties.

**Deploy:** The agent goes to production. The contract is referenced in the deployment configuration.

**Monitor:** Operational metrics (availability, latency, error rate) are tracked against SLA. Incidents trigger the accountability and escalation paths declared in the contract.

**Quarterly Review (or as scheduled):** The governance team reviews the contract against current agent behavior. Changes in scope, ownership, or authority require a new contract version.

**Update or Retire:** When the agent's scope changes, the contract is updated. When the agent is decommissioned, the contract is updated to `lifecycle.status: retired` with a `retirement_date`.

---

## When to Use Which Agent Type

| Type | When to Use | Example |
|------|-------------|---------|
| `autonomous` | Agent acts continuously without human triggers | Fraud scoring, monitoring, batch processing |
| `hybrid` | Agent triggered by humans but acts autonomously within scope | Support agent, document processor, workflow automator |
| `advisory` | Agent produces recommendations; humans make all decisions | Risk analysis, credit assessment, diagnostic support |

The type field has governance implications. `autonomous` agents typically require more rigorous authority boundaries and blast radius documentation because they can act at scale without a human checkpoint. `advisory` agents may have high risk tiers despite never taking direct actions — because their recommendations influence consequential decisions.

---

## Common Mistakes

**Mistake 1: Naming a team as primary owner**
Teams do not respond to incidents at 2 AM. Name a person.

**Mistake 2: Using vague scope limits**
"Cannot do anything harmful" is not a scope limit. "Cannot process refunds above $500 without manager approval" is.

**Mistake 3: Writing a generic blast radius**
"Could affect customers" is not a blast radius narrative. "Could affect all 50,000 active checkout sessions, resulting in failed payments at a rate of $2M/hour" is.

**Mistake 4: Skipping the retirement plan**
Every agent should have a planned end state. Agents without retirement criteria run forever, accumulate debt, and eventually fail in ways no one expected.

**Mistake 5: Treating the contract as a one-time artifact**
Contracts must be updated when ownership changes, scope changes, or the agent's behavior changes. A stale contract is worse than no contract — it provides false assurance.

---

## Further Reading

- [docs/PRINCIPLES.md](PRINCIPLES.md) — The four core AOF principles
- [docs/SCHEMA.md](SCHEMA.md) — Complete field reference
- [docs/COMPLIANCE.md](COMPLIANCE.md) — Regulatory framework mappings
- [docs/INTEGRATION.md](INTEGRATION.md) — Runtime and CI/CD integration
- [templates/contract-template.yaml](../templates/contract-template.yaml) — Blank contract to fill in
- [templates/contract-checklist.md](../templates/contract-checklist.md) — Pre-launch checklist
