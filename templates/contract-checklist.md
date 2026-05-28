# AOF Contract Pre-Launch Checklist

Use this checklist before deploying any AI agent to production. Each question maps to a section of the `AgentOwnershipContract`. Check every box. If you cannot check a box, resolve the gap before launching.

---

## Question 1: Who Owns This Agent?

- [ ] A named individual (not a team or alias) is declared as `ownership.primary_owner`
- [ ] The primary owner has been notified they are the owner and accepts accountability
- [ ] The primary owner's email is current and monitored
- [ ] The escalation path has at least one level with a current contact
- [ ] All escalation path contacts have been notified they are on the escalation list
- [ ] Ownership transfer procedure is documented (what happens when the owner leaves)

---

## Question 2: What Is This Agent Authorized to Do?

- [ ] All five authority flags (`can_initiate_actions`, `can_approve_actions`, `can_read_data`, `can_write_data`, `can_delegate`) are set explicitly
- [ ] `authority.scope_limits` has at least one specific, actionable constraint
- [ ] Scope limits are written as "Cannot X" statements, not vague restrictions
- [ ] The agent's actual code behavior matches the declared authority (no shadow permissions)
- [ ] Financial thresholds (if applicable) are declared in scope_limits (e.g., "Cannot approve amounts > $500")

---

## Question 3: What Data Can This Agent Access?

- [ ] `compliance.data_classification` is set to the appropriate sensitivity level
- [ ] `compliance.pii_handling` describes specifically what PII the agent touches
- [ ] `compliance.pii_handling` describes how that PII is protected (masking, tokenization, access controls)
- [ ] The agent has been verified to access only the data sources listed in `dependencies.data_sources`
- [ ] No data sources accessible to the agent are missing from the contract

---

## Question 4: What Happens When This Agent Fails?

- [ ] `accountability.incident_contact` is a monitored email that triggers an alert
- [ ] The incident contact has been tested — sending to it actually alerts someone
- [ ] `accountability.runbook_url` points to an actual, written runbook (not a placeholder)
- [ ] The runbook covers: how to diagnose, how to restart, how to engage the kill switch
- [ ] `accountability.on_call_rotation` is set and the rotation is active
- [ ] `risk.kill_switch_owner` is a named individual with the access to execute the shutdown

---

## Question 5: Who Reviews This Agent and How Often?

- [ ] `governance.review_cadence` is set appropriately for the risk tier
- [ ] `governance.change_control_board` names a real governing body
- [ ] The change control board knows it has governance authority for this agent
- [ ] `governance.approval_required_for` lists the specific change types requiring approval
- [ ] `governance.next_review` is set and on the calendar
- [ ] A recurring calendar event has been created for the next review

---

## Question 6: What Compliance Frameworks Apply?

- [ ] `compliance.frameworks` lists every applicable regulatory framework
- [ ] The legal and compliance team has reviewed the frameworks list
- [ ] `compliance.audit_log_required` is set to `true` if required by any listed framework
- [ ] `compliance.retention_policy` cites the specific regulation and retention period
- [ ] Any GDPR-regulated processing has a documented legal basis
- [ ] Any FCRA-regulated use has adverse action procedures documented

---

## Question 7: What Is the Blast Radius?

- [ ] `risk.risk_tier` is set and has been validated by the primary owner and a risk stakeholder
- [ ] `risk.blast_radius` is at least 50 characters and is specific (not vague)
- [ ] The blast radius describes scope of impact (users, money, systems)
- [ ] The blast radius describes the worst case, not the expected case
- [ ] The blast radius mentions regulatory implications if applicable
- [ ] The blast radius includes a recovery time estimate
- [ ] `risk.human_in_the_loop_required` is set correctly and matches actual agent behavior

---

## Question 8: How Is This Agent Retired?

- [ ] `lifecycle.status` is set to the correct current status (`active`, `pilot`, etc.)
- [ ] `lifecycle.deployed_at` is set to the deployment date
- [ ] A retirement plan exists (even if informal) for when this agent will be replaced
- [ ] The primary owner can articulate the criteria for retiring this agent
- [ ] If a replacement agent is planned, `lifecycle.replacement_agent_id` is set

---

## Technical Validation

- [ ] The contract passes schema validation: `python tools/validate-contract.py <contract.yaml>`
- [ ] All email fields contain valid, monitored email addresses
- [ ] `sla.availability` is a number (e.g., `99.9`), not a string (e.g., `"99.9%"`)
- [ ] All escalation path levels are sequential starting at 1
- [ ] The contract is committed to version control
- [ ] CI/CD validation is configured to validate this contract on every PR

---

## Sign-Off

| Role | Name | Email | Date |
|------|------|-------|------|
| Primary Owner | | | |
| Change Control Board | | | |
| Compliance Review | | | |
| Security Review (if risk_tier high/critical) | | | |

---

*If any checklist item cannot be checked, document why and obtain explicit approval to proceed. Unresolved items represent governance gaps that should be tracked to resolution.*
