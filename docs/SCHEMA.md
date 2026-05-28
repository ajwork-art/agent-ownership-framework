# Schema Field Reference

Complete field-by-field reference for AOF v1 (`apiVersion: aof/v1`). Every field in the `agent-ownership-contract.schema.json` is documented here with type, requirement status, valid values, and examples.

---

## Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `apiVersion` | string | Yes | Must be `aof/v1` |
| `kind` | string | Yes | Must be `AgentOwnershipContract` |
| `metadata` | object | Yes | Contract document metadata |
| `agent` | object | Yes | Agent identity and classification |
| `ownership` | object | Yes | Owner assignment and escalation |
| `authority` | object | Yes | Agent authority boundaries |
| `accountability` | object | Yes | Incident response contacts |
| `governance` | object | Yes | Review cadence and change control |
| `lifecycle` | object | Yes | Deployment status and retirement |
| `compliance` | object | Yes | Regulatory and data handling |
| `risk` | object | Yes | Risk tier, blast radius, kill switch |
| `dependencies` | object | Yes | Models, services, data sources |
| `sla` | object | Yes | Service level agreement |

---

## metadata

Metadata about the contract document itself — not the agent software.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `metadata.name` | string | Yes | Pattern: `^[a-z0-9][a-z0-9\-]*[a-z0-9]$` | Unique kebab-case slug identifying this contract. Use the agent's function. |
| `metadata.version` | string | Yes | Pattern: `^\d+\.\d+\.\d+$` | Semantic version of the CONTRACT document, not the agent code. |
| `metadata.created` | string | Yes | Format: date (YYYY-MM-DD) | Date this contract was first created. |
| `metadata.updated` | string | Yes | Format: date (YYYY-MM-DD) | Date of the most recent change to this contract. |
| `metadata.labels` | object | No | Values must be strings | Key-value pairs for filtering and tooling (env, team, cost-center). |
| `metadata.annotations` | object | No | Values must be strings | Non-identifying supplementary metadata (ticket URLs, wiki links). |

**Example:**

```yaml
metadata:
  name: fraud-detection-agent        # kebab-case, unique
  version: 3.0.1                      # contract version (not agent version)
  created: "2024-11-01"
  updated: "2026-03-15"
  labels:
    env: production
    team: risk-engineering
  annotations:
    jira-epic: "RISK-2201"
```

**Common variations:**
- `metadata.version` increments with every meaningful change: patch for edits, minor for new fields, major for ownership transfer
- `metadata.labels` is commonly used for filtering in CI/CD and dashboards
- `metadata.name` must match `agent.id` by convention

---

## agent

Describes the AI agent itself: what it is, what it does, and how it is classified.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `agent.id` | string | Yes | Pattern: `^[a-z0-9][a-z0-9\-]*[a-z0-9]$` | Globally unique agent identifier. Appears in logs, alerts, dashboards. |
| `agent.name` | string | Yes | minLength: 5 | Human-readable display name. |
| `agent.description` | string | Yes | minLength: 50 | What this agent does AND does not do. |
| `agent.type` | string | Yes | Enum: `autonomous`, `hybrid`, `advisory` | Operational classification. |
| `agent.domain` | string | Yes | — | Business domain (e.g., `financial-services`, `customer-service`). |
| `agent.tags` | array | No | Items are strings | Free-form tags for search and categorization. |

**agent.type values:**

| Value | Meaning |
|-------|---------|
| `autonomous` | Agent acts continuously without human triggers |
| `hybrid` | Agent triggered by humans but acts autonomously within scope |
| `advisory` | Agent produces recommendations only; humans make all decisions |

**Example:**

```yaml
agent:
  id: fraud-detection-agent
  name: Fraud Detection Agent
  description: >
    Real-time fraud scoring for card-present and card-not-present transactions.
    Returns a risk score within 150ms. Does not block or approve transactions —
    scoring only. Does not store raw card data.
  type: autonomous
  domain: financial-services
  tags:
    - fraud
    - real-time
    - pci-scope
```

**Common variations:**
- `agent.description` should explicitly state what the agent does NOT do — this is as important as what it does
- `agent.domain` should use consistent values across your organization
- `agent.id` must match `metadata.name`

---

## ownership

Declares who is responsible for the agent. Every agent must have exactly one named primary owner — a person, not a team.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `ownership.primary_owner` | object | Yes | — | The single named human accountable for this agent. |
| `ownership.primary_owner.name` | string | Yes | — | Full name. |
| `ownership.primary_owner.email` | string | Yes | Format: email | Current work email address. |
| `ownership.primary_owner.team` | string | Yes | — | Team or squad name. |
| `ownership.primary_owner.org` | string | Yes | — | Business unit or organizational unit. |
| `ownership.secondary_owners` | array | No | Items are owner objects | Additional named owners sharing operational responsibility. |
| `ownership.escalation_path` | array | Yes | minItems: 1 | Ordered escalation contacts. Levels must be sequential starting at 1. |
| `ownership.escalation_path[].level` | integer | Yes | minimum: 1 | Escalation level. Must be sequential (1, 2, 3...). |
| `ownership.escalation_path[].name` | string | Yes | — | Full name of escalation contact. |
| `ownership.escalation_path[].email` | string | Yes | Format: email | Email of escalation contact. |
| `ownership.escalation_path[].role` | string | Yes | — | Title or role of escalation contact. |

**Example:**

```yaml
ownership:
  primary_owner:
    name: Michael Chang
    email: michael.chang@example.com
    team: Risk Engineering
    org: Financial Crime Prevention
  escalation_path:
    - level: 1
      name: Jennifer Walsh
      email: jennifer.walsh@example.com
      role: VP Risk Engineering
    - level: 2
      name: Patricia Nguyen
      email: patricia.nguyen@example.com
      role: Chief Risk Officer
```

**Common mistakes:**
- Using a team alias as `primary_owner.email` — must be a real person's email
- Skipping escalation levels (e.g., 1, 3) — must be sequential
- Not updating the escalation path when people change roles

---

## authority

Declares what the agent is explicitly permitted to do. Follows least-privilege: if not declared as allowed, it is not allowed.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `authority.can_initiate_actions` | boolean | Yes | — | Can the agent act autonomously without human triggers? |
| `authority.can_approve_actions` | boolean | Yes | — | Can the agent approve actions (its own or others')? |
| `authority.can_read_data` | boolean | Yes | — | Can the agent read from data sources? |
| `authority.can_write_data` | boolean | Yes | — | Can the agent write to or modify data? |
| `authority.can_delegate` | boolean | Yes | — | Can the agent spawn sub-agents or delegate? |
| `authority.scope_limits` | array | Yes | minItems: 1 | Plain-language constraints on what the agent cannot do. |

**Example:**

```yaml
authority:
  can_initiate_actions: true
  can_approve_actions: false
  can_read_data: true
  can_write_data: true
  can_delegate: false
  scope_limits:
    - "Cannot process refunds above $500 without human approval"
    - "Cannot access raw card numbers — tokenized references only"
    - "Cannot contact customers outside business hours 8am-10pm"
```

**Common variations:**
- `advisory` agents almost always have `can_approve_actions: false` and `can_write_data: false`
- `scope_limits` should be written as "Cannot X" statements for clarity
- Even if `can_write_data: true`, add scope limits that specify which systems the agent can write to

---

## accountability

Defines incident response contacts, on-call rotation, and post-mortem requirements.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `accountability.incident_contact` | string | Yes | Format: email | Primary email for production incident alerts. |
| `accountability.on_call_rotation` | string | No | — | Name or URL of the on-call rotation schedule. |
| `accountability.runbook_url` | string | No | — | URL to the operational runbook for this agent. |
| `accountability.post_mortem_required` | boolean | Yes | — | Must a post-mortem be written after every production incident? |

**Example:**

```yaml
accountability:
  incident_contact: payments-oncall@example.com
  on_call_rotation: "Payments Platform On-Call — PagerDuty P1234AB"
  runbook_url: "https://wiki.example.com/display/PAY/payment-agent-runbook"
  post_mortem_required: true
```

**Guidance:**
- `incident_contact` should trigger an actual alert — not a monitored inbox checked once a day
- Set `post_mortem_required: true` for any agent with `risk_tier: medium` or above
- `runbook_url` should link to a document that exists, not a placeholder

---

## governance

Controls review cadence, change approval requirements, and the governing body.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `governance.review_cadence` | string | Yes | Enum: `weekly`, `monthly`, `quarterly`, `annually` | How often the contract and agent behavior must be formally reviewed. |
| `governance.approval_required_for` | array | Yes | minItems: 1 | Change types that require governance board approval. |
| `governance.change_control_board` | string | Yes | — | Name or contact of the governing body. |
| `governance.last_reviewed` | string | No | Format: date | Date of the most recent formal review. |
| `governance.next_review` | string | No | Format: date | Date of the next scheduled review. |

**Cadence guidance:**

| Risk Tier | Recommended Cadence |
|-----------|-------------------|
| critical | quarterly (minimum) |
| high | quarterly |
| medium | quarterly |
| low | annually |

**Example:**

```yaml
governance:
  review_cadence: quarterly
  approval_required_for:
    - "Model version change or retraining"
    - "New data source integration"
    - "Increase in financial transaction limits"
    - "Scope expansion beyond current payment types"
  change_control_board: "Payments Risk and Compliance Committee"
  last_reviewed: "2026-01-10"
  next_review: "2026-04-10"
```

---

## lifecycle

Tracks deployment status and the retirement plan.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `lifecycle.status` | string | Yes | Enum: `active`, `conditional`, `pilot`, `paused`, `retired` | Current lifecycle status. |
| `lifecycle.deployed_at` | string | No | Format: date | Date first deployed to production. |
| `lifecycle.deprecated_at` | string | No | — | Date deprecated (still running, no new traffic). |
| `lifecycle.retirement_date` | string | No | — | Planned full decommission date. |
| `lifecycle.replacement_agent_id` | string | No | — | agent.id of the replacement agent. |

**Status values:**

| Value | Meaning |
|-------|---------|
| `active` | In production, serving live traffic |
| `conditional` | In production with restrictions (limited users, features, or regions) |
| `pilot` | Experimental deployment, not in critical path |
| `paused` | Temporarily suspended, not serving traffic |
| `retired` | Fully decommissioned |

---

## compliance

Regulatory frameworks, data classification, PII handling, and audit requirements.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `compliance.frameworks` | array | Yes | minItems: 1, items are strings | Applicable regulatory frameworks. |
| `compliance.data_classification` | string | Yes | Enum: `public`, `internal`, `restricted`, `highly-restricted` | Sensitivity level of data the agent accesses. |
| `compliance.pii_handling` | string | Yes | minLength: 20 | Plain-language PII handling description. |
| `compliance.audit_log_required` | boolean | Yes | — | Must all agent actions be written to an immutable audit log? |
| `compliance.retention_policy` | string | Yes | minLength: 20 | Data retention requirements with regulatory basis. |

**data_classification values:**

| Value | Meaning |
|-------|---------|
| `public` | No access restrictions — data is publicly available |
| `internal` | Employee access only — no customer PII |
| `restricted` | Limited access with explicit controls — customer PII or financial data |
| `highly-restricted` | Strongest controls, explicit authorization required — financial crime data, health data |

**Common compliance frameworks:**

| Framework | Domain |
|-----------|--------|
| `SOX` | Financial reporting |
| `GLBA` | Financial services — customer data |
| `PCI-DSS` | Payment card data |
| `BSA-AML` | Anti-money laundering |
| `GDPR` | EU personal data |
| `FCRA` | Consumer credit reporting |
| `HIPAA` | Health information (US) |
| `ECOA` | Equal credit opportunity |
| `EU-AI-Act` | EU AI regulation |

---

## risk

Risk profile of the agent: tier, blast radius, human oversight requirements, and kill switch.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `risk.risk_tier` | string | Yes | Enum: `low`, `medium`, `high`, `critical` | Risk classification. |
| `risk.blast_radius` | string | Yes | minLength: 50 | Worst-case impact if the agent fails or is compromised. |
| `risk.human_in_the_loop_required` | boolean | Yes | — | Must humans approve consequential actions before execution? |
| `risk.kill_switch_owner` | string | No | Format: email | Email of the person authorized to immediately disable this agent. |

**Risk tier guidance:**

| Tier | Typical Characteristics |
|------|------------------------|
| `low` | Internal-only, no customer PII, no financial impact, recoverable instantly |
| `medium` | Customer-facing, limited financial exposure, contained blast radius |
| `high` | Significant customer or financial impact, regulatory implications |
| `critical` | Existential business risk, major regulatory exposure, platform-wide impact |

**Blast radius writing guidance:**
- State the scope of impact (how many users, how much money, which systems)
- State the worst case, not the expected case
- State the regulatory implications if applicable
- State the recovery time estimate

---

## dependencies

External models, services, and data sources the agent depends on.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `dependencies.models` | array | No | Items are dependency objects | LLMs or ML models used by the agent. |
| `dependencies.services` | array | No | Items are dependency objects | Internal or external services called by the agent. |
| `dependencies.data_sources` | array | No | Items are dependency objects | Databases, streams, or datasets read by the agent. |

**Dependency object fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Name of the dependency. |
| `version` | string | No | Version or release identifier. |
| `type` | string | No | Category: `llm`, `ml-model`, `rest-api`, `postgresql`, `kafka`, etc. |
| `description` | string | No | What this dependency is used for. |

---

## sla

Service level agreement for the agent's production operation.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `sla.availability` | number | Yes | 0 ≤ value ≤ 100 | Target availability as a percentage NUMBER. Not a string. |
| `sla.max_latency_ms` | integer | Yes | minimum: 1 | Maximum acceptable end-to-end latency in milliseconds. |
| `sla.error_rate_threshold` | string | No | — | Maximum acceptable error rate as a human-readable string. |
| `sla.throughput_limit` | string | No | — | Maximum request throughput as a human-readable string. |

**IMPORTANT:** `sla.availability` must be a NUMBER like `99.9`, not a string like `"99.9%"`. This is the most common schema validation error.

**Common availability values:**

| Value | Meaning | Max downtime/year |
|-------|---------|------------------|
| 99.9 | Three nines | ~8.7 hours |
| 99.5 | — | ~43.8 hours |
| 99.0 | Two nines | ~87.6 hours |
| 95.0 | — | ~438 hours |
| 99.99 | Four nines | ~52 minutes |

**Example:**

```yaml
sla:
  availability: 99.9       # NUMBER, not "99.9%"
  max_latency_ms: 4000
  error_rate_threshold: "0.5%"
  throughput_limit: "2000 concurrent sessions"
```
