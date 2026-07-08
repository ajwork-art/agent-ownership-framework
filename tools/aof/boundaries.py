"""
Eight-boundary governance checklist for AOF contracts.

Each ``_bN_*`` function checks one of the eight AOF governance boundaries and
returns a :class:`Boundary` with per-item pass/fail results. Used by
``aof check``.

Author: Anitha Jagadeesh — Enterprise Data AI Realities
License: MIT
"""

from typing import Any, Dict, List, Tuple


# ---------------------------------------------------------------------------
# Safe accessors for nested YAML data
# ---------------------------------------------------------------------------

def _str(obj: Any, *keys: str, default: str = "") -> str:
    for k in keys:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(k, default)
    return obj if isinstance(obj, str) else default


def _list(obj: Any, *keys: str) -> List:
    for k in keys:
        if not isinstance(obj, dict):
            return []
        obj = obj.get(k, [])
    return obj if isinstance(obj, list) else []


def _dict(obj: Any, *keys: str) -> Dict:
    for k in keys:
        if not isinstance(obj, dict):
            return {}
        obj = obj.get(k, {})
    return obj if isinstance(obj, dict) else {}


class Boundary:
    """Result of checking a single governance boundary."""

    def __init__(self, number: int, name: str) -> None:
        self.number = number
        self.name = name
        self.items: List[Tuple[bool, str]] = []

    def ok(self, msg: str) -> None:
        self.items.append((True, msg))

    def fail(self, msg: str) -> None:
        self.items.append((False, msg))

    @property
    def passed(self) -> bool:
        return bool(self.items) and all(ok for ok, _ in self.items)


def _b1_purpose(c: Dict) -> Boundary:
    b = Boundary(1, "Purpose")
    p = _dict(c, "purpose")

    bp = _str(p, "business_purpose").strip()
    if len(bp) >= 50:
        b.ok(f"Business purpose: {len(bp)} chars")
    elif bp:
        b.fail(f"Business purpose too short: {len(bp)} chars (minimum 50)")
    else:
        b.fail("Business purpose not defined — add purpose.business_purpose")

    metrics = _dict(p, "success_metrics")
    if metrics:
        b.ok(f"Success metrics: {len(metrics)} defined")
    else:
        b.fail("Success metrics not defined — add measurable outcome targets")

    oos = _list(p, "out_of_scope")
    if oos:
        b.ok(f"Out-of-scope list: {len(oos)} explicit exclusion(s)")
    else:
        b.fail("Out-of-scope list is empty — add 'Cannot X' exclusions")

    return b


def _b2_ownership(c: Dict) -> Boundary:
    b = Boundary(2, "Ownership")
    own = _dict(c, "ownership")

    for label, key in [("Domain owner", "domain_owner"), ("Technical owner", "technical_owner")]:
        owner = _dict(own, key)
        name = _str(owner, "name").strip()
        email = _str(owner, "email").strip()
        if name and email:
            b.ok(f"{label}: {name} ({email})")
        elif name:
            b.fail(f"{label} '{name}' is missing an email address")
        else:
            b.fail(f"{label} not defined — add ownership.{key} with name and email")

    return b


def _b3_authority(c: Dict) -> Boundary:
    b = Boundary(3, "Authority")
    auth = _dict(c, "authority")

    decisions = _list(auth, "autonomous_decisions")
    if decisions:
        b.ok(f"Autonomous decisions: {len(decisions)} defined")
    else:
        b.fail("No autonomous decisions — list what the agent can decide without human approval")

    prohibited = _list(auth, "prohibited_actions")
    if prohibited:
        b.ok(f"Prohibited actions: {len(prohibited)} defined")
    else:
        b.fail("No prohibited actions — add hard limits the agent can never cross")

    triggers = _list(auth, "escalation_triggers")
    if triggers:
        b.ok(f"Escalation triggers: {len(triggers)} defined")
    else:
        b.fail("No escalation triggers — specify conditions that force human review")

    override = _dict(auth, "override_mechanism")
    pausers = _list(override, "who_can_pause")
    overrider = _str(override, "who_can_override").strip()
    if pausers and overrider:
        b.ok(f"Override mechanism: {len(pausers)} pause role(s), override role named")
    else:
        missing = []
        if not pausers:
            missing.append("who_can_pause")
        if not overrider:
            missing.append("who_can_override")
        b.fail(f"Override mechanism incomplete — missing: {', '.join(missing)}")

    return b


def _b4_data(c: Dict) -> Boundary:
    b = Boundary(4, "Data")
    data = _dict(c, "data")

    permitted = _list(data, "permitted_sources")
    if permitted:
        b.ok(f"Permitted sources: {len(permitted)} defined")
    else:
        b.fail("No permitted data sources — list every source the agent may access")

    prohibited = _list(data, "prohibited_sources")
    if prohibited:
        b.ok(f"Prohibited sources: {len(prohibited)} defined")
    else:
        b.fail("No prohibited data sources — explicitly exclude off-limits data")

    handling = _dict(data, "sensitive_data_handling")
    if handling:
        mask = _list(handling, "must_mask")
        detail = f"{len(mask)} field(s) masked" if mask else "configured"
        b.ok(f"Sensitive data handling rules: {detail}")
    else:
        b.fail("No sensitive data handling rules — add data.sensitive_data_handling")

    return b


def _b5_escalation(c: Dict) -> Boundary:
    b = Boundary(5, "Escalation Path")
    path = _list(_dict(c, "ownership"), "escalation_path")

    if path:
        levels = [e.get("level") for e in path if isinstance(e, dict) and "level" in e]
        noun = "level" if len(path) == 1 else "levels"
        b.ok(f"Escalation path: {len(path)} {noun} defined {levels}")
    else:
        b.fail("Escalation path not defined — add ownership.escalation_path with ordered contacts")

    return b


def _b6_incident_response(c: Dict) -> Boundary:
    b = Boundary(6, "Incident Response")
    ir = _dict(c, "incident_response")

    investigator = _str(ir, "investigator_primary").strip()
    if investigator:
        b.ok(f"Primary investigator: {investigator}")
    else:
        b.fail("Primary investigator not defined — add incident_response.investigator_primary")

    scope = _list(ir, "investigation_scope")
    if len(scope) >= 3:
        b.ok(f"Investigation scope: {len(scope)} questions defined")
    elif scope:
        b.fail(f"Investigation scope: {len(scope)} question(s) — minimum 3 required")
    else:
        b.fail("Investigation scope not defined — list what the investigation must answer")

    comm = _dict(ir, "communication")
    cust = _str(comm, "customer_owner").strip()
    stake = _str(comm, "stakeholder_owner").strip()
    compl = _str(comm, "compliance_owner").strip()
    if cust and stake and compl:
        b.ok("Communication owners: customer, stakeholder, and compliance defined")
    else:
        missing = [name for name, val in
                   [("customer_owner", cust), ("stakeholder_owner", stake), ("compliance_owner", compl)]
                   if not val]
        b.fail(f"Communication owners incomplete — missing: {', '.join(missing)}")

    return b


def _b7_governance(c: Dict) -> Boundary:
    b = Boundary(7, "Governance")
    gov = _dict(c, "governance")

    cadence = _str(gov, "review_cadence").strip()
    if cadence:
        b.ok(f"Review cadence: {cadence}")
    else:
        b.fail("Review cadence not defined — add governance.review_cadence")

    board = _str(gov, "change_control_board").strip()
    if board:
        b.ok(f"Change control board: {board}")
    else:
        b.fail("Change control board not named — add governance.change_control_board")

    approval = _list(gov, "approval_required_for")
    if approval:
        b.ok(f"Approval required for: {len(approval)} change type(s)")
    else:
        b.fail("No approval requirements — specify what changes need governance board approval")

    signoff = _dict(c, "signoff")
    d_name = _str(signoff, "domain_owner", "name").strip()
    t_name = _str(signoff, "technical_owner", "name").strip()
    if d_name and t_name:
        b.ok(f"Signoff: {d_name} (domain) and {t_name} (technical)")
    elif d_name or t_name:
        missing = "technical_owner" if d_name else "domain_owner"
        b.fail(f"Signoff incomplete — {missing} has not signed")
    else:
        b.fail("No signoffs — domain_owner and technical_owner must sign before launch")

    return b


def _b8_compliance(c: Dict) -> Boundary:
    b = Boundary(8, "Compliance")
    comp = _dict(c, "compliance")

    frameworks = _list(comp, "frameworks")
    if frameworks:
        b.ok(f"Compliance frameworks: {', '.join(str(f) for f in frameworks)}")
    else:
        b.fail("No compliance frameworks listed — add applicable regulations (SOX, GDPR, etc.)")

    classification = _str(comp, "data_classification").strip()
    if classification:
        b.ok(f"Data classification: {classification}")
    else:
        b.fail("Data classification not set — choose: public, internal, restricted, highly-restricted")

    audit = comp.get("audit_log_required")
    if audit is not None:
        b.ok(f"Audit log required: {str(audit).lower()}")
    else:
        b.fail("Audit log requirement not declared — set compliance.audit_log_required")

    return b


def run_all_boundaries(contract: Dict) -> List[Boundary]:
    return [
        _b1_purpose(contract),
        _b2_ownership(contract),
        _b3_authority(contract),
        _b4_data(contract),
        _b5_escalation(contract),
        _b6_incident_response(contract),
        _b7_governance(contract),
        _b8_compliance(contract),
    ]
