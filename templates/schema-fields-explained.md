# Schema Fields Explained (Plain English)

This document explains every section of an AOF contract in plain English — no jargon, no code. This is for business owners, product managers, compliance leads, and legal reviewers who need to understand and approve agent contracts without reading the technical specification.

---

## The Big Picture

An AOF contract is a document that answers eight questions about an AI agent before it goes into production. Think of it like a product specification combined with an operating license. Just as a building needs a permit that specifies its purpose, its owner, its safety features, and its inspections — an AI agent needs a contract that specifies the same.

---

## Section: Metadata

**What it is:** The "cover page" of the contract document.

**Business relevance:** Metadata identifies the contract and tracks when it was last updated. If someone asks "when was this agent last reviewed?" — the answer is in the metadata.

**Key fields:**
- **name** — A short, unique identifier for the agent (like a file name). Example: `fraud-detection-agent`
- **version** — Tracks how many times this contract has been changed. A version of `2.1.0` means major updates have happened since it was first written.
- **created / updated** — When the contract was written and last changed. If `updated` is more than a year old, the contract is likely stale.
- **labels** — Tags for organizing agents (which team owns it, which environment it runs in).

---

## Section: Agent

**What it is:** The description of what the agent actually is and does.

**Business relevance:** This is the scope document. It defines what the agent is built to do — and critically, what it is NOT built to do. Vague descriptions here lead to scope creep and liability later.

**Key fields:**
- **name** — The display name for the agent. What shows up in dashboards and incident tickets.
- **description** — 2-3 sentences describing what the agent does and what it does not do. This is the most important field for non-technical readers. A good description is specific: "Processes refunds up to $500. Does NOT modify account settings or approve refunds above $500."
- **type** — How the agent operates:
  - **Autonomous** — Acts on its own without a human pressing a button for each action
  - **Hybrid** — A human starts the process, then the agent acts on its own within limits
  - **Advisory** — Only gives recommendations; humans make every actual decision
- **domain** — The business area (customer service, financial services, operations)

---

## Section: Ownership

**What it is:** The answer to "who is responsible?"

**Business relevance:** This is the most important section from a governance perspective. Named ownership is what makes accountability real. Teams that resist naming an owner for an agent are implicitly admitting that no one wants to be responsible for its decisions.

**Key fields:**
- **primary_owner** — One specific person, with their name and email. Not a team. Not an alias. A person. This is the individual who answers for this agent when something goes wrong.
- **secondary_owners** — Optional co-owners who share operational responsibility but are not the primary accountability holder.
- **escalation_path** — If you cannot reach the primary owner in an emergency, who do you call next? And after that? The escalation path defines this sequence. Level 1 is first, level 2 is second, and so on. Each level must have a real person's name and current email.

---

## Section: Authority

**What it is:** The operating license — what the agent is explicitly allowed to do.

**Business relevance:** Most AI governance failures happen because no one explicitly defined what the agent could and could not do. This section forces that conversation before deployment. It follows the principle of least privilege: the agent should have exactly the authority it needs, and nothing more.

**Key fields:**
- **can_initiate_actions** — Can the agent do things on its own without being asked? (True for autonomous agents, false for advisory ones)
- **can_approve_actions** — Can the agent say "yes" to something? For example, can it approve a refund, or does a human always need to approve?
- **can_read_data** — Can the agent look at data? (Almost always yes)
- **can_write_data** — Can the agent change data, create records, or modify systems? (This is the dangerous one — should be explicitly limited)
- **can_delegate** — Can the agent hand work off to other AI agents?
- **scope_limits** — The "cannot do" list. These are the specific things the agent is explicitly prohibited from doing. Examples: "Cannot process refunds above $500." "Cannot access employee records." "Cannot contact customers outside business hours."

---

## Section: Accountability

**What it is:** The emergency response plan.

**Business relevance:** When an AI agent fails in production at 2 AM, who gets called? What do they do? This section pre-answers those questions so that the response is organized, not improvised.

**Key fields:**
- **incident_contact** — The email address that gets an alert when the agent has a problem. This must be a real, monitored address that triggers an actual response — not an inbox checked once a week.
- **on_call_rotation** — The name of the on-call schedule so responders know who is covering each shift.
- **runbook_url** — A link to written instructions for what to do when the agent fails. A runbook can be a simple wiki page: "Step 1: Check the logs. Step 2: Restart the service. Step 3: If problem persists, escalate to [name]."
- **post_mortem_required** — Must the team write a root cause analysis after every incident? For medium-risk and higher agents, this should always be yes. Without post-mortems, failures repeat.

---

## Section: Governance

**What it is:** The review schedule and change approval process.

**Business relevance:** AI agents change over time — the models get updated, the data changes, the team changes. Governance defines how often someone formally checks that the agent is still behaving appropriately, and what changes require formal approval.

**Key fields:**
- **review_cadence** — How often the agent must be formally reviewed (weekly, monthly, quarterly, annually). Higher risk = more frequent review.
- **approval_required_for** — A list of specific change types that require a sign-off from the governance board before implementation. Examples: "Model version update," "New data source integration," "Expansion of refund authority."
- **change_control_board** — The name of the governing body that approves changes. This might be an existing committee (risk committee, tech governance board) or a new one.
- **last_reviewed / next_review** — The dates of the most recent review and the next scheduled one. If `next_review` has passed, the contract is overdue for review.

---

## Section: Lifecycle

**What it is:** The current operational status and retirement plan.

**Business relevance:** Agents without a clear retirement plan run forever, accumulate technical debt, and eventually fail in ways no one anticipated. This section forces teams to think about the end state from the beginning.

**Key fields:**
- **status** — Where is the agent in its lifecycle?
  - **active** — Running in production, serving live traffic
  - **conditional** — Running with restrictions (limited users, pilot features)
  - **pilot** — Experimental deployment, not in the critical path
  - **paused** — Temporarily shut down
  - **retired** — Permanently decommissioned
- **deployed_at** — When the agent was first launched to production.
- **retirement_date** — When the agent will be turned off. May not be known at launch, but should be set when deprecation begins.
- **replacement_agent_id** — What replaces this agent when it is retired.

---

## Section: Compliance

**What it is:** The regulatory obligations and data handling requirements.

**Business relevance:** This section is where the legal and compliance team's input is most important. It documents which regulations apply, how sensitive the data is, how customer data is protected, and what audit records must be kept.

**Key fields:**
- **frameworks** — The list of regulations this agent must comply with. Examples: SOX (financial reporting), GLBA (banking customer data), PCI-DSS (credit cards), GDPR (EU personal data), HIPAA (health information), FCRA (credit reporting).
- **data_classification** — How sensitive is the data the agent handles?
  - **public** — Freely available information, no restrictions
  - **internal** — Employee-only information, no customer data
  - **restricted** — Customer data or financial data with access controls
  - **highly-restricted** — The most sensitive data (health records, financial crime data) with the strictest controls
- **pii_handling** — In plain language: what personally identifiable information does the agent touch, and how is it protected? Is it masked in logs? Is it stored? Is it shared with anyone?
- **audit_log_required** — Must every action the agent takes be recorded in an unchangeable log? Many regulations require this.
- **retention_policy** — How long must records be kept, and why? The "why" should cite the specific regulation.

---

## Section: Risk

**What it is:** The honest assessment of what could go wrong.

**Business relevance:** This section is where governance adds the most value — and where teams most often want to be vague. A specific, honest risk assessment makes it possible to have a real conversation about whether the agent is worth the risk, and what safeguards are needed.

**Key fields:**
- **risk_tier** — The overall risk level (low, medium, high, critical). This should be set by the primary owner and validated by a risk stakeholder, not self-assessed by the building team alone.
- **blast_radius** — What is the worst case if this agent fails or is compromised? Be specific. "Could affect customers" is not acceptable. "Could affect all 50,000 active checkout sessions, resulting in failed payments at a rate of $2M/hour, triggering PCI-DSS incident notification requirements" is.
- **human_in_the_loop_required** — Must a human review and approve what the agent does before it acts? For advisory agents, this is always yes. For high-volume autonomous agents, it may be no — but that decision must be explicitly stated and justified.
- **kill_switch_owner** — Who can turn this agent off immediately in an emergency, without going through normal approval processes? This person must have the technical access to do so and must be reachable at any hour.

---

## Section: Dependencies

**What it is:** The list of everything the agent depends on.

**Business relevance:** If any of these dependencies goes down or changes, the agent is affected. This section documents the supply chain of the agent — useful for incident response, for understanding risk propagation, and for change management.

**Key fields:**
- **models** — The AI models the agent uses (large language models, machine learning models). Tracking model versions is important for governance — a model update can change the agent's behavior significantly.
- **services** — The external APIs and internal services the agent calls (payment gateways, CRM systems, data services).
- **data_sources** — The databases and data streams the agent reads from.

---

## Section: SLA

**What it is:** The performance guarantees for the agent in production.

**Business relevance:** SLA targets define expectations for reliability and speed. They also define what counts as a failure — if the SLA says 99.9% availability and the agent is down 5% of the time, that is a breach requiring a governance response.

**Key fields:**
- **availability** — What percentage of time must the agent be operational? 99.9% means it can be down at most about 9 hours per year. Written as a number, not a string with a percent sign.
- **max_latency_ms** — The maximum time (in milliseconds) the agent should take to respond. For a customer-facing chat agent, this might be 4,000ms (4 seconds). For a fraud detector, it might be 150ms.
- **error_rate_threshold** — What percentage of requests can fail before it becomes a problem worth escalating?
- **throughput_limit** — Is there a maximum volume of requests the agent can handle? Useful for preventing runaway automated callers from overwhelming the agent.
