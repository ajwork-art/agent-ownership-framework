# Compliance Framework Mappings

How AOF contract fields map to regulatory requirements across common compliance frameworks. Use this document to identify which fields you must complete to support a specific compliance audit.

> **Note:** This document provides guidance, not legal advice. Consult your compliance and legal team for requirements specific to your jurisdiction, business model, and regulatory relationship.

---

## SOX (Sarbanes-Oxley Act)

**Applicable to:** Public companies and their subsidiaries in the US. Agents that affect financial reporting, controls, or records.

| SOX Requirement | AOF Field | How It Supports Compliance |
|----------------|-----------|---------------------------|
| Control ownership (Section 302) | `ownership.primary_owner` | Named individual certifies control existence and effectiveness |
| Change control (ITGC) | `governance.approval_required_for`, `governance.change_control_board` | Documents what changes require approval and who approves |
| Audit trail (Section 802) | `compliance.audit_log_required: true` | All agent actions logged to immutable storage |
| Record retention (Section 802) | `compliance.retention_policy` | 7-year retention for financial records |
| Access controls | `authority.can_write_data`, `authority.scope_limits` | Declares write authority boundaries |
| Incident response | `accountability.incident_contact`, `accountability.runbook_url` | Defined response procedures for control failures |
| Periodic review | `governance.review_cadence`, `governance.last_reviewed` | Demonstrates ongoing control monitoring |

**Key fields for SOX agents:**

```yaml
compliance:
  frameworks: [SOX]
  audit_log_required: true
  retention_policy: >
    All agent transaction records and decision logs retained for 7 years
    per SOX Section 802. Stored in WORM-compliant audit storage.

governance:
  review_cadence: quarterly
  approval_required_for:
    - "Changes to financial calculation logic"
    - "New data source affecting financial records"
  change_control_board: "Finance IT Governance Committee"
```

---

## GLBA (Gramm-Leach-Bliley Act)

**Applicable to:** Financial institutions handling customer financial data. Banks, insurers, securities firms, and fintech companies.

| GLBA Requirement | AOF Field | How It Supports Compliance |
|-----------------|-----------|---------------------------|
| Safeguards Rule — ownership | `ownership.primary_owner` | Named individual accountable for customer data protection |
| Safeguards Rule — access controls | `authority.can_read_data`, `authority.scope_limits` | Limits access to minimum necessary data |
| Safeguards Rule — monitoring | `accountability.incident_contact`, `governance.review_cadence` | Ongoing monitoring and incident response |
| Privacy Rule — PII handling | `compliance.pii_handling` | Documents how NPI (nonpublic personal information) is handled |
| Data classification | `compliance.data_classification` | Identifies sensitivity of customer financial data |
| Breach response | `accountability.escalation_path` | Escalation path for potential data incidents |

**Key fields for GLBA agents:**

```yaml
compliance:
  frameworks: [GLBA]
  data_classification: restricted  # or highly-restricted for sensitive NPI
  pii_handling: >
    Agent accesses customer account numbers and transaction history (NPI under GLBA).
    Data accessed through role-based controls. Account numbers masked in logs.
    NPI not shared with third parties without customer consent.
  audit_log_required: true
  retention_policy: >
    Customer financial data records retained per applicable GLBA requirements.
    Audit logs of NPI access retained for 5 years.
```

---

## PCI-DSS (Payment Card Industry Data Security Standard)

**Applicable to:** Any organization that stores, processes, or transmits payment card data. Agents in the payment processing scope.

| PCI-DSS Requirement | AOF Field | How It Supports Compliance |
|--------------------|-----------|---------------------------|
| Requirement 7 — Restrict data access | `authority.scope_limits` | Documents that agent cannot access raw PAN, CVV |
| Requirement 8 — Identify and authenticate | `ownership.primary_owner`, `accountability.incident_contact` | Accountability for authorized access |
| Requirement 10 — Track and monitor access | `compliance.audit_log_required: true` | All access to cardholder data logged |
| Requirement 12 — Security policies | `governance.change_control_board`, `governance.approval_required_for` | Change management for systems in PCI scope |
| Tokenization scope | `agent.tags` (pci-scope tag), `compliance.pii_handling` | Documents tokenization approach |
| Incident response | `accountability.runbook_url`, `accountability.on_call_rotation` | Documented IR procedures |

**Key fields for PCI-DSS agents:**

```yaml
metadata:
  labels:
    pci-scope: "true"  # Mark all agents in PCI scope

agent:
  tags: [pci-scope]

compliance:
  frameworks: [PCI-DSS]
  data_classification: highly-restricted
  pii_handling: >
    Agent receives tokenized payment credentials only. Raw PAN, CVV, and
    expiry dates are never accessible. Tokenization is handled upstream by
    the PCI-DSS Level 1 certified token vault.
  audit_log_required: true

authority:
  scope_limits:
    - "Cannot access raw card numbers (PAN) — tokenized references only"
    - "Cannot access CVV or card security codes"
```

---

## GDPR (General Data Protection Regulation)

**Applicable to:** Organizations processing personal data of EU/EEA residents, regardless of where the organization is based.

| GDPR Requirement | AOF Field | How It Supports Compliance |
|-----------------|-----------|---------------------------|
| Accountability (Art. 5(2)) | `ownership.primary_owner` | Named DPO or data controller equivalent |
| Purpose limitation (Art. 5(1)(b)) | `agent.description`, `authority.scope_limits` | Documents specific purpose of data processing |
| Data minimization (Art. 5(1)(c)) | `authority.can_read_data`, `compliance.pii_handling` | Limits data access to minimum necessary |
| Storage limitation (Art. 5(1)(e)) | `compliance.retention_policy` | Documents retention periods |
| Right to erasure (Art. 17) | `compliance.retention_policy` | Documents erasure procedures |
| Data breach notification | `accountability.incident_contact`, `ownership.escalation_path` | Response path for potential breaches |
| DPIA (Art. 35) | `risk.blast_radius`, `risk.risk_tier` | Risk assessment supporting DPIA |
| Automated decision-making (Art. 22) | `risk.human_in_the_loop_required`, `agent.type` | Declares whether human review applies |

**Key fields for GDPR agents:**

```yaml
compliance:
  frameworks: [GDPR]
  pii_handling: >
    Agent processes EU resident personal data including name, email, and
    behavioral data for [specific purpose]. Legal basis: legitimate interest /
    contract performance. Data subjects may request erasure via privacy@company.com.
    Data not transferred outside EU without SCCs in place.
  retention_policy: >
    Personal data retained for [X] years per [legal basis]. GDPR erasure requests
    processed within 30 days. Audit logs retain only pseudonymized identifiers.

risk:
  human_in_the_loop_required: true  # Required for Art. 22 automated decision-making
```

---

## FCRA (Fair Credit Reporting Act)

**Applicable to:** Consumer reporting agencies and users of consumer reports. Agents that use credit information to make or influence decisions about consumers.

| FCRA Requirement | AOF Field | How It Supports Compliance |
|-----------------|-----------|---------------------------|
| Permissible purpose | `agent.description`, `authority.scope_limits` | Documents permissible purpose for accessing consumer reports |
| Accuracy (Section 607) | `risk.human_in_the_loop_required`, `governance.review_cadence` | Human review of consequential decisions |
| Adverse action notice | `compliance.pii_handling` | Documents adverse action procedures |
| Consumer rights | `compliance.pii_handling` | Documents how consumer rights are handled |
| Audit trail | `compliance.audit_log_required: true` | Log of all consumer report access |
| Retention | `compliance.retention_policy` | 5-year retention for consumer report records |

**Key fields for FCRA agents:**

```yaml
compliance:
  frameworks: [FCRA]
  audit_log_required: true
  pii_handling: >
    Agent accesses consumer credit report data for [permissible purpose per FCRA].
    SSNs masked (last 4 only). Adverse action notices generated per FCRA
    requirements when agent output contributes to an adverse decision.
  retention_policy: >
    Consumer credit assessment records retained for 5 years per FCRA requirements.
    Adverse action records retained for 5 years.

risk:
  human_in_the_loop_required: true  # All adverse actions require human review
```

---

## HIPAA (Health Insurance Portability and Accountability Act)

**Applicable to:** Covered entities (health plans, healthcare providers, clearinghouses) and their business associates handling PHI.

| HIPAA Requirement | AOF Field | How It Supports Compliance |
|------------------|-----------|---------------------------|
| Minimum necessary (§164.502(b)) | `authority.scope_limits`, `compliance.pii_handling` | Limits access to minimum necessary PHI |
| Access controls (§164.312(a)) | `authority.can_read_data`, `ownership.primary_owner` | Named accountability for PHI access |
| Audit controls (§164.312(b)) | `compliance.audit_log_required: true` | All PHI access logged |
| Integrity controls | `governance.review_cadence`, `governance.approval_required_for` | Change management for PHI systems |
| Breach notification | `accountability.incident_contact`, `ownership.escalation_path` | Defined response for potential breaches |
| BAA tracking | `metadata.annotations` | Can reference BAA document URLs |
| Retention (6 years) | `compliance.retention_policy` | HIPAA requires 6-year retention |

**Key fields for HIPAA agents:**

```yaml
compliance:
  frameworks: [HIPAA, HITECH]
  data_classification: highly-restricted
  pii_handling: >
    Agent accesses Protected Health Information (PHI) including diagnosis codes,
    treatment history, and medication records. Access limited to minimum necessary
    for [clinical purpose]. PHI not used for secondary purposes. All access by
    authorized workforce members only.
  audit_log_required: true
  retention_policy: >
    PHI access logs and agent decision records retained for 6 years per HIPAA
    §164.530(j). PHI itself retained per covered entity's retention schedule.

risk:
  risk_tier: critical
  human_in_the_loop_required: true  # Clinician always reviews AI recommendations
```

---

## EU AI Act

**Applicable to:** Organizations deploying AI systems in the EU. High-risk AI systems (credit scoring, employment, education, law enforcement, biometrics, critical infrastructure) face the strictest requirements.

| EU AI Act Requirement | AOF Field | How It Supports Compliance |
|----------------------|-----------|---------------------------|
| Risk classification (Art. 6) | `risk.risk_tier`, `agent.domain` | Documents risk classification basis |
| Human oversight (Art. 14) | `risk.human_in_the_loop_required` | Declares human oversight posture |
| Transparency (Art. 13) | `agent.description`, `compliance.pii_handling` | Documents system behavior |
| Data governance (Art. 10) | `compliance.data_classification`, `dependencies.data_sources` | Data quality and governance documentation |
| Technical documentation (Art. 11) | `dependencies.models`, `governance.review_cadence` | Model documentation and monitoring |
| Incident reporting (Art. 62) | `accountability.incident_contact`, `accountability.post_mortem_required` | Incident response procedures |
| Conformity assessment | `governance.change_control_board`, `governance.approval_required_for` | Change control procedures |
| Post-market monitoring | `governance.next_review`, `sla` | Ongoing performance monitoring |

**Key fields for EU AI Act high-risk systems:**

```yaml
compliance:
  frameworks: [EU-AI-Act, GDPR]

agent:
  description: >
    [Must clearly describe the system's purpose, intended use, and limitations
    per Art. 13 transparency requirements]

risk:
  human_in_the_loop_required: true  # Required for high-risk AI under Art. 14

governance:
  review_cadence: quarterly  # Required ongoing monitoring

accountability:
  post_mortem_required: true  # Supports Art. 62 incident reporting
```

---

## Common Compliance Scenarios

### Financial Services — Full Stack

An agent handling customer financial decisions (loan approvals, fraud flags, account actions) typically requires:

```yaml
compliance:
  frameworks: [SOX, GLBA, FCRA, PCI-DSS]  # Stack as applicable
  data_classification: restricted           # or highly-restricted
  audit_log_required: true
  retention_policy: "7 years per SOX; 5 years per FCRA; masked within 90 days per GLBA"

risk:
  risk_tier: high  # or critical
  human_in_the_loop_required: true

governance:
  review_cadence: quarterly
```

### Healthcare

Clinical decision support, triage, or patient communication agents require:

```yaml
compliance:
  frameworks: [HIPAA, HITECH]
  data_classification: highly-restricted
  audit_log_required: true
  retention_policy: "6 years per HIPAA §164.530(j)"

risk:
  risk_tier: critical
  human_in_the_loop_required: true  # Clinician always decides
```

### SaaS / Consumer Tech (EU Users)

Consumer-facing agents handling EU user data:

```yaml
compliance:
  frameworks: [GDPR, CCPA]
  data_classification: restricted
  pii_handling: "... includes EU resident erasure procedures ..."
  retention_policy: "Data retained per legitimate interest basis; erasure within 30 days"

risk:
  human_in_the_loop_required: true  # For Art. 22 automated decision-making
```
