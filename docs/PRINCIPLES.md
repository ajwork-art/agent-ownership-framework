# AOF Core Principles

The Agent Ownership Framework is built on four principles. Every design decision in the schema, the tooling, and the examples flows from these four commitments.

---

## Principle 1: Ownership Is Explicit

**Every agent has a named human owner. Not a team. Not a system. A person.**

### Why It Matters

When an agent fails in production, the first question is: who owns this? If the answer is "the platform team" or "we all do," no one acts with urgency. Responsibility that belongs to everyone belongs to no one.

Named ownership creates clarity. One person is accountable for the agent's behavior — for its decisions, its failures, and its compliance posture. That accountability motivates the owner to understand the agent's scope, set appropriate authority limits, and maintain the contract over time.

Explicit ownership also enables incident response. When the agent causes harm at 2 AM, there is exactly one person to call. That person has agreed — by signing off on the contract — that they are the right person to call.

### What It Means in Practice

- The primary owner must be a named individual with a current work email
- The primary owner should be the person accountable for the *business decisions* the agent makes, not just the person who runs the infrastructure
- When the primary owner changes roles or leaves, the contract must be updated immediately — a stale owner is a governance failure
- Secondary owners are supplementary, not substitutes for primary accountability

### Schema Fields

```yaml
ownership:
  primary_owner:
    name: Jane Smith              # Named individual
    email: jane.smith@company.com # Current, monitored email
    team: Payments Platform
    org: Engineering
```

### Real Example

A fraud detection agent is built by the Risk Engineering team and hosted by the Platform team. Both teams could claim ownership. AOF forces the question: who is accountable if this agent incorrectly flags a legitimate transaction at scale and causes customer harm? The answer is the Risk Engineering VP — not the Platform team — because it is a business risk decision. The contract reflects that.

---

## Principle 2: Authority Is Bounded

**Agents operate within explicitly declared, least-privilege authority bounds.**

### Why It Matters

An agent without declared authority limits will expand into whatever it can access. This is not malice — it is the natural result of deploying a system with broad capability and no documented constraints. Over time, the agent accumulates implicit permissions, accesses more data sources, and takes on more consequential actions. No one knows what it is actually authorized to do anymore.

Bounded authority prevents this. By declaring exactly what the agent can and cannot do — in a contract, at deployment, not just in code — teams create a documented scope that can be reviewed, audited, and enforced.

Bounded authority also forces a conversation that teams often skip: what does this agent actually need? Most agents need far less authority than they are given. The discipline of filling out the `authority` section reveals scope creep before it becomes a compliance problem.

### What It Means in Practice

- Every agent has explicit boolean flags for read/write/approve/delegate authority
- The `scope_limits` list documents what the agent cannot do — in plain language, not code
- Authority limits should be set conservatively at launch and expanded only through the governance process
- "Can do anything the task requires" is not a scope limit — it is an absence of one

### Schema Fields

```yaml
authority:
  can_initiate_actions: true
  can_approve_actions: false      # Explicit: agent cannot approve
  can_read_data: true
  can_write_data: false           # Explicit: agent cannot write
  can_delegate: false

  scope_limits:
    - "Cannot process refunds above $500 — requires human approval"
    - "Cannot access raw card numbers — tokenized references only"
    - "Cannot contact customers outside business hours"
```

### Real Example

A customer support agent is deployed with `can_write_data: true` for writing case notes. Without explicit scope limits, the same write access could theoretically modify account balances, update billing information, or change subscription plans. The `scope_limits` list makes clear that write access is limited to the CRM case management system only — and explicitly excludes billing and account management.

---

## Principle 3: Accountability Is Enforced

**Violations are detected, logged, and escalated. Accountability is not a statement of intent — it is a mechanism.**

### Why It Matters

Declaring that someone is accountable for an agent means nothing if violations are not detected and if there is no mechanism to escalate when something goes wrong. Many organizations have governance documents that list owners and responsibilities but have no monitoring, no incident contact, and no runbook. When something fails, the governance document is irrelevant — no one knows to look at it.

AOF makes accountability operational. The contract declares an incident contact, an on-call rotation, and an escalation path — so that when the agent fails, the response path is predetermined, not improvised.

Post-mortem requirements create accountability over time. If every incident requires a written post-mortem, teams are incentivized to understand root causes and prevent recurrence. Without this requirement, incidents are fixed silently and the lessons are lost.

### What It Means in Practice

- `accountability.incident_contact` must be a monitored email address that triggers alerts
- `accountability.on_call_rotation` should link to an actual on-call schedule (PagerDuty, OpsGenie, etc.)
- `accountability.runbook_url` should link to an actual runbook — not a placeholder
- `accountability.post_mortem_required: true` for any agent with risk_tier medium or above
- The escalation path should be realistic: the people listed must know they are on the escalation path

### Schema Fields

```yaml
accountability:
  incident_contact: payments-oncall@company.com
  on_call_rotation: "Payments Platform On-Call — PagerDuty P1234AB"
  runbook_url: "https://wiki.company.com/payments-agent-runbook"
  post_mortem_required: true

ownership:
  escalation_path:
    - level: 1
      name: Robert Kim
      email: robert.kim@company.com
      role: Director of Payments Engineering
    - level: 2
      name: Sarah Wong
      email: sarah.wong@company.com
      role: VP Engineering
```

### Real Example

A fraud detection agent at a financial institution has `post_mortem_required: true` and a documented escalation path reaching the Chief Risk Officer at level 3. When the fraud model has a latency spike that causes scoring timeouts, the incident contact is paged immediately, the on-call engineer follows the runbook to diagnose, and the Director of Risk Engineering is escalated within 30 minutes. Without the declared escalation path, that escalation would take hours as engineers try to find the right person.

---

## Principle 4: Evidence Is Retained

**All agent decisions are auditable. Evidence is not optional for consequential agents.**

### Why It Matters

Regulated industries require audit trails. Even outside regulated industries, the ability to reconstruct what an agent decided, when, and why is essential for debugging, improving, and defending those decisions.

When an agent is involved in a dispute — a customer challenging a refund denial, a regulator questioning a credit decision, an internal team investigating a fraud miss — the ability to reconstruct the agent's decision process is the difference between resolution and liability.

Evidence retention is also the mechanism by which agents become trustworthy over time. If every decision is logged, teams can analyze patterns, identify drift, and detect systematic failures. Without logs, agents are black boxes that cannot be improved or held accountable.

### What It Means in Practice

- `compliance.audit_log_required: true` for any agent with risk_tier medium or above
- `compliance.retention_policy` must specify the retention period and the regulatory basis for it
- Audit logs should include input, output, decision rationale, and timestamp — not just action taken
- For regulated domains, the retention policy must match the applicable regulation (7 years for SOX, 5 years for FCRA, etc.)
- Logs containing PII must comply with data minimization requirements (mask or anonymize PII in logs)

### Schema Fields

```yaml
compliance:
  audit_log_required: true

  retention_policy: >
    Transaction records and agent decision logs retained for 7 years per SOX
    Section 802 requirements. PII elements purged after 90 days unless required
    for active dispute resolution. Audit logs stored in WORM-compliant storage.
```

### Real Example

A risk analysis agent produces credit risk assessments that influence loan decisions. Under FCRA, adverse action against a credit applicant must be explainable. When an applicant challenges a denial, the compliance team needs to reconstruct exactly which risk factors the agent flagged, what signals it weighted, and what recommendation it produced. Without `audit_log_required: true` and a retention policy covering the full regulatory period, that reconstruction is impossible — and the institution faces FCRA liability.

---

## How the Principles Connect

The four principles are interdependent:

- **Ownership** without **accountability** is a name on paper with no operational meaning
- **Authority** without **evidence** cannot be audited — you cannot prove the agent stayed within bounds
- **Accountability** without **ownership** has no one to hold accountable
- **Evidence** without **ownership** produces logs that no one is responsible for reviewing

A complete AOF contract satisfies all four — which is why every section of the schema is required for medium-risk and above agents.
