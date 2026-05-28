# Frequently Asked Questions

---

**Q: What is the Agent Ownership Framework?**

AOF is a contract schema and toolchain for declaring who owns an AI agent, what it is authorized to do, and how it is governed. It is modeled after the data contract movement but applied to AI agents rather than data assets. The core artifact is an `AgentOwnershipContract` — a YAML file that answers the eight ownership questions before an agent goes to production.

---

**Q: Who needs AOF?**

Any organization deploying AI agents with meaningful authority: agents that approve transactions, access customer data, send communications, modify records, or make recommendations that influence consequential decisions. If the agent does something that would matter if it failed or was compromised, it needs a contract.

---

**Q: How long does it take to write a contract?**

For a familiar agent with a known owner and clear scope, 30-60 minutes. For a complex agent in a regulated domain, 2-4 hours including compliance framework mapping and stakeholder review. The template and examples are designed to minimize blank-page friction.

---

**Q: Can I use AOF for a proof-of-concept or demo agent?**

AOF is designed for production agents. For PoC and demo agents, a minimal contract (filling in `agent`, `ownership`, and `risk` at minimum) is still worthwhile — it forces the "what would production governance look like?" conversation early, which is valuable.

---

**Q: How does AOF relate to data contracts?**

Data contracts (ODCS and similar open standards) govern data assets — what the data contains, who produces it, and what quality is promised. AOF governs agents — entities that consume data assets and take actions. They are complementary: a well-governed data platform has both data contracts on its datasets and ownership contracts on the agents that use those datasets.

---

**Q: How does AOF relate to NIST AI RMF?**

NIST AI RMF provides a framework for AI risk management across the organization. AOF implements the "GOVERN" and "MANAGE" functions of the RMF at the individual agent level. The AOF contract is a concrete artifact that demonstrates GOVERN function compliance: documented ownership, authority, risk assessment, and governance cadence.

---

**Q: How does AOF relate to the EU AI Act?**

The EU AI Act requires technical documentation, transparency, human oversight, and incident reporting for high-risk AI systems. AOF fields map directly to these requirements — see [docs/COMPLIANCE.md](COMPLIANCE.md) for the field-by-field mapping. An AOF contract is not sufficient for EU AI Act compliance on its own, but it satisfies several documentation and governance requirements.

---

**Q: What happens when a primary owner leaves the company?**

The contract must be updated within 30 days. This is a governance failure if it happens without a transfer — the escalation path should include someone who can identify and onboard a new owner. Consider adding contract review to offboarding checklists for any role that owns production agents.

---

**Q: Can a team be the primary owner?**

No. AOF requires a named individual — a specific person with a name and email address. Teams do not respond to incidents with urgency because responsibility diffused across a group belongs to no one. The named primary owner is the person who, at 2 AM when the agent fails, gets the call.

---

**Q: What is the difference between primary and secondary owners?**

The primary owner is the single named human who is ultimately accountable. Secondary owners share operational responsibility — they may co-own the on-call rotation, review the contract, or substitute when the primary owner is unavailable. But when accountability is required, it goes to the primary owner.

---

**Q: Can the same agent have different contracts for different environments (staging vs production)?**

Yes. Contracts can be scoped by environment using `metadata.labels.env: staging` vs `env: production`. The production contract should be the most complete and most reviewed. Staging contracts may have relaxed SLAs and different owners but should still declare authority bounds.

---

**Q: What if our agent's authority boundaries are not clearly defined?**

Then the agent should not be in production. The discipline of filling out `authority.scope_limits` often reveals that the team has not made explicit decisions about what the agent is and is not allowed to do. Make those decisions before deployment, not after an incident.

---

**Q: How often should contracts be reviewed?**

- `critical` risk agents: quarterly minimum
- `high` risk agents: quarterly
- `medium` risk agents: quarterly
- `low` risk agents: annually

Reviews should be triggered by: model updates, scope changes, ownership changes, incident post-mortems, and regulatory changes. The scheduled cadence is the minimum.

---

**Q: Does the agent code need to reference the contract?**

At minimum, the contract should be version-controlled alongside the agent code. Ideally, the application loads the contract at startup and uses it to enforce authority limits at runtime (see [docs/INTEGRATION.md](INTEGRATION.md) for examples). The contract should never drift from the agent's actual behavior.

---

**Q: Can I validate contracts in a language other than Python or Node.js?**

The schema is standard JSON Schema draft-07, which has validators in Go, Java, .NET, Ruby, and many other languages. The schema file at `schema/v1/agent-ownership-contract.schema.json` can be used with any JSON Schema validator. The Python and Node.js tools are provided as reference implementations.

---

**Q: What makes a good blast_radius narrative?**

A good blast radius is specific about scope (how many users, how much money, which systems), honest about worst case (not expected case), mentions regulatory implications if applicable, and gives a recovery time estimate. Vague statements like "could affect customers" are not acceptable. See the fraud-detection-agent example for a model blast radius narrative.

---

**Q: What if our agent is advisory — it only makes recommendations? Does it need a full contract?**

Yes. Advisory agents carry risk even though they do not take direct actions — because their recommendations influence consequential decisions. A risk analysis agent that produces systematically biased credit assessments causes real harm even if humans make the final call. Advisory agents with `risk_tier: high` require the same governance rigor as autonomous agents. The difference is `human_in_the_loop_required: true` and `authority.can_approve_actions: false`.

---

**Q: How do we handle agents that call other agents?**

The calling agent's contract should declare `authority.can_delegate: true` if it spawns or calls other agents. Each sub-agent should have its own contract. The calling agent's `dependencies.services` or `dependencies.models` section should reference the sub-agents it calls. Ownership does not transfer through delegation — each agent has its own owner.

---

**Q: Does AOF work for vendor AI systems we have configured (e.g., Salesforce Einstein, Microsoft Copilot)?**

Yes. If your organization has configured a vendor AI system with specific authority (access to your customer data, ability to take actions in your systems), it needs an ownership contract. The `agent.description` should note that it is a vendor system. Your organization is responsible for how you have configured it — even if the underlying model is vendor-provided.

---

**Q: What is the kill switch, and when is it used?**

The `risk.kill_switch_owner` is the named person authorized to immediately disable the agent in production — bypassing normal change management. The kill switch is used in incidents where the agent is causing active harm and must be stopped before a full root cause analysis. This person must be reachable at any hour and must have the technical access to execute the shutdown. The kill switch owner is often (but not always) the primary owner.

---

**Q: Is AOF open source? Can we fork it?**

Yes. AOF is MIT licensed. You may fork, modify, and use it in your own products. Attribution to the original author (Anitha Jagadeesh, Enterprise Data AI Realities) is appreciated but not required by the license. If you build something useful on top of AOF, consider contributing it back to the community.

---

**Q: How does versioning work when we update a contract?**

Follow semantic versioning: patch for minor edits (typos, label changes), minor for meaningful changes (ownership update, new optional fields, scope adjustment), major for structural changes (agent completely redesigned, new agent type). Every change must update `metadata.updated` to today's date.

---

**Q: Can we automate contract generation from agent code or configuration?**

Yes. Several community implementations generate draft contracts from agent configurations. The generated output should always be reviewed by the named primary owner before being committed — a generated contract is a starting point, not a finished governance artifact. Key fields like `risk.blast_radius` and `authority.scope_limits` require human judgment that cannot be automated.
