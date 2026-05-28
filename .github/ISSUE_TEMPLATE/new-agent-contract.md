---
name: New Agent Contract
about: Use this template when creating a new AOF contract for an AI agent
title: "feat: add ownership contract for [AGENT NAME]"
labels: new-contract
assignees: ""
---

## Agent Description

<!-- Describe what this agent does in 2-3 sentences. Include what it does NOT do. -->

## Owner Assignment

**Proposed primary owner:**
- Name:
- Email:
- Team:
- Organization:

**Why this person?**
<!-- Explain why this individual is the appropriate primary owner (what business decisions does the agent make that this person is accountable for?) -->

## Data Access Needed

**What data does this agent need to read?**
<!-- List data sources, databases, APIs, streams -->

**What data does this agent need to write or modify?**
<!-- If none, say "None — read only" -->

**Does this agent access any PII?**
<!-- If yes, describe what PII and how it will be protected -->

## Tools and Actions

**What actions can this agent take autonomously?**
<!-- Be specific. This becomes scope_limits in the contract. -->

**What actions require human approval?**
<!-- These become the human_in_the_loop requirements -->

**What is this agent explicitly prohibited from doing?**
<!-- These become scope_limits -->

## Risk Assessment

**Proposed risk tier:** [ ] low  [ ] medium  [ ] high  [ ] critical

**Blast radius (worst case if this agent fails or is compromised):**
<!-- Be specific: number of affected users, financial exposure, regulatory implications, recovery time -->

**Does this agent require a human to approve actions before execution?**
[ ] Yes  [ ] No

**Justification if No:**
<!-- If HITL not required, explain why -->

## Compliance Requirements

**What compliance frameworks apply?**
- [ ] SOX
- [ ] GLBA
- [ ] PCI-DSS
- [ ] GDPR
- [ ] FCRA
- [ ] HIPAA
- [ ] BSA-AML
- [ ] EU AI Act
- [ ] Internal policy only
- [ ] Other: _______________

**Data classification:**
- [ ] public
- [ ] internal
- [ ] restricted
- [ ] highly-restricted

**Is an audit log required?**
[ ] Yes  [ ] No

## SLA Targets

**Target availability (%):** ___
**Maximum latency (ms):** ___

## Checklist Before Submitting PR

- [ ] Contract drafted using `templates/contract-template.yaml`
- [ ] All required fields filled in (no placeholders remaining)
- [ ] Contract passes validation: `python tools/validate-contract.py <contract.yaml>`
- [ ] Primary owner has reviewed and approved
- [ ] Compliance review completed (if regulated domain)
- [ ] Added to `examples/README.md` if contributing as an example
