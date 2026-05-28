# AOF Enterprise Implementation Guide

A week-by-week roadmap for adopting the Agent Ownership Framework across an organization. This guide assumes an organization with existing production AI agents and a need to establish formal governance.

---

## Before You Start

**Prerequisite: Executive sponsorship**

AOF adoption requires someone with organizational authority to say: "No agent goes to production without a contract." This is typically a CTO, CRO, or Chief AI Officer. Without this mandate, the process stalls when teams push back on governance overhead.

**What you will produce:**
- A complete inventory of production AI agents
- Named owners for each agent
- Validated AOF contracts for each agent
- A CI/CD validation pipeline
- A recurring governance review process

**Typical timeline:** 7 weeks for the initial implementation. Ongoing: quarterly reviews.

---

## Week 1: Agent Inventory

**Goal:** Know what agents exist.

Most organizations do not have a complete inventory of their production AI agents. Discovery is the most important and often most surprising step.

**Activities:**

1. **Identify all AI systems in production.** Include:
   - LLM-based agents and chatbots
   - ML models making autonomous decisions
   - Automation scripts with database write access or external API calls
   - Vendor AI systems your organization has configured (Salesforce Einstein, Microsoft Copilot, etc.)
   - "Shadow AI" — agents deployed by individual teams without central awareness

2. **Create an inventory spreadsheet** with columns:
   - Agent name / description
   - Business domain
   - Estimated risk tier
   - Team that deployed it
   - Estimated primary owner
   - Current governance status (none / informal / formal)

3. **Identify the gaps.** Flag agents with no clear owner. Flag agents with no documentation. These are the highest-risk items.

**Deliverable:** A spreadsheet of every production AI agent with estimated owners and risk tiers.

**Common findings:** Teams typically discover 20-50% more agents than leadership knew existed. Shadow AI in internal tooling and operations is common.

---

## Weeks 2-3: Assign Owners

**Goal:** Every agent has a named primary owner who accepts accountability.

**Activities:**

1. **Review the inventory with business stakeholders.** For each agent, ask: "If this agent causes customer harm or a regulatory violation, who answers for it?" That person (or their direct report) is the primary owner.

2. **Assign draft ownership.** Do not let teams assign ownership to team aliases or shared mailboxes. A person must be named.

3. **Notify draft owners.** Send each draft primary owner:
   - What the agent does
   - Why they are being nominated as owner
   - What ownership means (they will be contacted in incidents, they must sign the contract)

4. **Resolve ownership disputes.** When two teams both claim or both disclaim ownership, use the business decision rule: who is accountable for the decisions this agent makes? That is the owner.

5. **Identify agents with no viable owner.** If no one will accept ownership, the agent should be paused until ownership is established. An unowned production agent is ungoverned.

**Deliverable:** Updated inventory with named primary owners confirmed by those individuals.

---

## Weeks 4-5: Draft Contracts

**Goal:** A validated AOF contract for every production agent.

**Activities:**

1. **Assign contract drafters.** Each primary owner (or a designated drafter on their team) fills out the contract template. Use the examples closest to their agent type as a starting point.

2. **Hold drafting office hours.** Make someone available for 1-2 hours per day to answer questions. Common questions: "What goes in blast_radius?" "How specific do scope_limits need to be?" "Which compliance frameworks apply to us?"

3. **Run validation frequently.** Drafters should run `python tools/validate-contract.py` on their drafts daily. Fix schema errors early.

4. **Prioritize by risk tier.** Start with critical agents, then high, then medium, then low. If time is constrained, get critical agents done first.

5. **Do not let drafters skip the hard fields.** `risk.blast_radius` and `authority.scope_limits` are where governance adds the most value — and where teams most want to be vague. Require specificity.

**Deliverable:** Draft contracts for all agents, passing schema validation.

---

## Week 6: Review with Legal, Compliance, and Security

**Goal:** Contracts reviewed and signed by appropriate stakeholders before committal.

**Activities:**

1. **Legal review** (for regulated agents):
   - Are the compliance frameworks listed correctly?
   - Is the pii_handling narrative accurate and legally defensible?
   - Is the retention_policy consistent with legal obligations?

2. **Compliance review:**
   - Does the contract reflect actual regulatory requirements?
   - Are audit requirements set correctly (audit_log_required)?
   - Is the governance cadence sufficient for the regulatory context?

3. **Security review** (for risk_tier high and critical):
   - Is the authority scope appropriately bounded?
   - Is the data classification correct?
   - Is the kill switch process operational?

4. **Fix gaps found in review.** Update contracts and re-validate.

**Deliverable:** Contracts reviewed and approved by legal/compliance/security where applicable.

---

## Week 7: Sign-Off, Commit, and Enforce

**Goal:** Contracts are live, version-controlled, and enforced in CI/CD.

**Activities:**

1. **Primary owner sign-off.** Each primary owner reviews their final contract and approves via PR merge (or documented sign-off process).

2. **Commit contracts to version control.** All contracts live in Git alongside the agent code — or in a dedicated contracts repository.

3. **Deploy CI/CD validation.** Add the GitHub Actions or GitLab CI workflow (see `ci-cd/`) so that any PR modifying a contract triggers automated validation. PRs with invalid contracts are blocked.

4. **Configure pre-commit hooks** (optional but recommended) so validation runs before every commit.

5. **Communicate the mandate.** Publish the new policy: "From [date], all production AI agents must have a valid AOF contract. New agents may not go to production without one."

**Deliverable:** All contracts committed, CI/CD enforcing validation, policy communicated.

---

## Ongoing: Monitor and Review

**Goal:** Contracts stay current as agents evolve.

**Quarterly (or per cadence):**
- Review each contract against actual agent behavior — has anything changed?
- Run `python tools/validate-contract.py examples/*.yaml` to confirm no contracts have drifted from schema
- Check `governance.next_review` dates — schedule reviews before they expire
- Update `governance.last_reviewed` and `governance.next_review` after each review

**Event-triggered reviews** (these require a contract update, not just a calendar review):
- Owner changes role or leaves the company
- Agent's authority scope changes (new data access, new actions)
- Model version update or retraining
- New regulatory requirement applies
- Significant incident with post-mortem findings that affect governance

**Retire agents properly:**
- Update `lifecycle.status: retired`
- Set `lifecycle.retirement_date`
- Set `lifecycle.replacement_agent_id` if applicable
- Archive the contract in version control — do not delete it

---

## Metrics to Track

Once AOF is implemented, track these governance metrics:

| Metric | Target | Notes |
|--------|--------|-------|
| % of production agents with valid contracts | 100% | Non-negotiable |
| % of contracts with upcoming review overdue | 0% | Check quarterly |
| % of incidents with named primary owner reachable | 100% | Monitor post-incident |
| Average time from incident to escalation | < 30 min | For critical agents |
| % of schema validation failures caught in CI/CD | 100% | Measures pipeline effectiveness |

---

## Common Obstacles and Responses

| Obstacle | Response |
|----------|----------|
| "This is too much overhead for small agents" | Low-risk internal agents have a minimal contract option. The template takes 30 minutes to fill out. |
| "We don't have a governance committee" | Assign an existing body (tech lead group, risk committee) to serve that function. |
| "The owner won't accept accountability" | This is a sign the agent should not be in production. Escalate to the executive sponsor. |
| "We don't know who owns it" | Pause the agent until ownership is established. Running unowned production agents is the governance failure AOF is designed to prevent. |
| "The compliance team is unavailable" | Proceed with draft contracts, mark compliance review as pending, and set a deadline for resolution before the next scheduled review. |
