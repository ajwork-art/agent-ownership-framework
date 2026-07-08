"""
Exporters for AOF contracts (``aof export --format ...``).

AOF performs deployment-time validation. These exporters generate **policy
inputs and documentation** from a validated contract; they do **not** enforce
anything at runtime. The generated OPA/Rego and A2A artifacts are starting
points for a separate runtime policy layer that a team owns and reviews.

Formats:
- ``markdown``  — a one-page human-readable ownership card (wikis, runbooks).
- ``a2a-card``  — an experimental A2A Agent Card JSON mapping of overlapping fields.
- ``opa``       — a Rego policy stub derived from the authority/data sections, with
                  TODO markers everywhere human review is required.

Author: Anitha Jagadeesh — Enterprise Data AI Realities
License: MIT
"""

import json
from typing import Any, Dict, List

from . import __version__


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _get(obj: Any, *keys: str, default: Any = None) -> Any:
    for k in keys:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(k, default)
    return obj


def _slug(text: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "-" for c in str(text))
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-") or "item"


# ---------------------------------------------------------------------------
# markdown ownership card
# ---------------------------------------------------------------------------

def to_markdown(contract: Dict[str, Any]) -> str:
    agent = contract.get("agent", {}) if isinstance(contract.get("agent"), dict) else {}
    ownership = contract.get("ownership", {}) if isinstance(contract.get("ownership"), dict) else {}
    risk = contract.get("risk", {}) if isinstance(contract.get("risk"), dict) else {}
    governance = contract.get("governance", {}) if isinstance(contract.get("governance"), dict) else {}
    authority = contract.get("authority", {}) if isinstance(contract.get("authority"), dict) else {}

    name = agent.get("name", agent.get("id", "Unnamed agent"))
    lines: List[str] = []
    lines.append(f"# Ownership Card — {name}")
    lines.append("")
    lines.append("> Generated from an AOF contract (deployment-time governance). "
                 "This card documents ownership and boundaries; it does not enforce them at runtime.")
    lines.append("")
    lines.append(f"- **Agent ID:** `{agent.get('id', '—')}`")
    lines.append(f"- **Type:** {agent.get('type', '—')}  ·  **Domain:** {agent.get('domain', '—')}")
    lines.append(f"- **Risk tier:** {risk.get('risk_tier', '—')}  ·  "
                 f"**Human-in-the-loop:** {risk.get('human_in_the_loop_required', '—')}")
    lines.append("")

    if agent.get("description"):
        lines.append("## Description")
        lines.append(str(agent["description"]).strip())
        lines.append("")

    lines.append("## Owners")
    for label, key in (("Domain owner", "domain_owner"), ("Technical owner", "technical_owner"),
                       ("Data owner", "data_owner"), ("Risk owner", "risk_owner")):
        owner = ownership.get(key)
        if isinstance(owner, dict) and owner.get("name"):
            email = owner.get("email", "")
            role = owner.get("role", "")
            suffix = f" — {role}" if role else ""
            lines.append(f"- **{label}:** {owner['name']} <{email}>{suffix}")
    lines.append("")

    escalation = ownership.get("escalation_path", [])
    if isinstance(escalation, list) and escalation:
        lines.append("## Escalation path")
        for i, e in enumerate(escalation, start=1):
            if isinstance(e, dict):
                # Use the contract's own escalation level, falling back to the
                # 1-based position, so entries render as 1., 2., 3. rather than
                # a repeated "1.".
                level = e.get("level", i)
                lines.append(f"{level}. {e.get('name', '—')} <{e.get('email', '')}> — {e.get('role', '')}")
        lines.append("")

    decisions = authority.get("autonomous_decisions", [])
    if isinstance(decisions, list) and decisions:
        lines.append("## Autonomous authority")
        for d in decisions:
            if isinstance(d, dict):
                limit = ""
                if d.get("limit") is not None:
                    inner = f"{d.get('limit')} {d.get('currency', '')}".strip()
                    limit = f" (limit: {inner})"
                lines.append(f"- `{d.get('decision_type', '—')}`{limit}")
        lines.append("")

    prohibited = authority.get("prohibited_actions", [])
    if isinstance(prohibited, list) and prohibited:
        lines.append("## Prohibited actions")
        for p in prohibited:
            lines.append(f"- {p}")
        lines.append("")

    if risk.get("blast_radius"):
        lines.append("## Blast radius")
        lines.append(str(risk["blast_radius"]).strip())
        lines.append("")

    lines.append("## Governance")
    lines.append(f"- **Review cadence:** {governance.get('review_cadence', '—')}")
    lines.append(f"- **Next review:** {governance.get('next_review', '—')}")
    lines.append(f"- **Change control board:** {governance.get('change_control_board', '—')}")
    if risk.get("kill_switch_owner"):
        lines.append(f"- **Kill switch owner:** {risk['kill_switch_owner']}")
    lines.append("")

    signoff = contract.get("signoff", {})
    if isinstance(signoff, dict) and signoff:
        lines.append("## Sign-off")
        for role, entry in signoff.items():
            if isinstance(entry, dict) and entry.get("name"):
                lines.append(f"- **{role}:** {entry['name']} ({entry.get('date', 'undated')})")
        lines.append("")

    lines.append("---")
    lines.append(f"*Generated by aof {__version__}. Source of truth is the AOF contract, not this card.*")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# A2A Agent Card (EXPERIMENTAL)
#
# Mapped against the Agent2Agent (A2A) Protocol specification, current stable
# version 1.0.0 (Linux Foundation). Verified 2026-07 at:
#   https://a2a-protocol.org/latest/specification/
# AgentCard top-level fields: name, description, version, protocolVersion, url,
# skills[{id,name,description,tags}], capabilities, defaultInputModes,
# defaultOutputModes, securitySchemes.
#
# EXPERIMENTAL: AOF and A2A model different concerns (governance vs. runtime
# discovery/interop). Only overlapping fields are mapped; A2A-required runtime
# fields that AOF does not model (url, securitySchemes) are emitted as empty
# placeholders under `x-aof` for a human to complete. Do not publish this card
# to a `/.well-known/agent-card.json` endpoint without review.
# ---------------------------------------------------------------------------

A2A_PROTOCOL_VERSION = "1.0.0"
A2A_SPEC_URL = "https://a2a-protocol.org/latest/specification/"


def to_a2a_card(contract: Dict[str, Any]) -> Dict[str, Any]:
    agent = contract.get("agent", {}) if isinstance(contract.get("agent"), dict) else {}
    metadata = contract.get("metadata", {}) if isinstance(contract.get("metadata"), dict) else {}
    authority = contract.get("authority", {}) if isinstance(contract.get("authority"), dict) else {}

    skills: List[Dict[str, Any]] = []
    for d in authority.get("autonomous_decisions", []) or []:
        if isinstance(d, dict) and d.get("decision_type"):
            skills.append({
                "id": _slug(d["decision_type"]),
                "name": d["decision_type"],
                "description": (d.get("description") or "").strip() or d["decision_type"],
                "tags": agent.get("tags", []) if isinstance(agent.get("tags"), list) else [],
            })

    card: Dict[str, Any] = {
        "protocolVersion": A2A_PROTOCOL_VERSION,
        "name": agent.get("name", agent.get("id", "")),
        "description": (agent.get("description") or "").strip(),
        "version": metadata.get("version", ""),
        "url": "",  # A2A requires a service endpoint; AOF does not model one.
        "capabilities": {},
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
        "skills": skills,
        "x-aof": {
            "experimental": True,
            "generated_by": f"aof {__version__}",
            "a2a_spec": A2A_SPEC_URL,
            "note": (
                "EXPERIMENTAL DRAFT MAPPING — not a publish-ready A2A Agent Card. "
                "This maps overlapping fields from an AOF governance contract; it is "
                "not a validated A2A document and AOF does not enforce at runtime. "
                "Fill in `url`, `capabilities`, and `securitySchemes`, validate against "
                "the A2A schema, and review before serving at /.well-known/agent-card.json."
            ),
            "source_agent_id": agent.get("id", ""),
        },
    }
    return card


# ---------------------------------------------------------------------------
# OPA / Rego policy stub
# ---------------------------------------------------------------------------

def to_opa_rego(contract: Dict[str, Any]) -> str:
    agent = contract.get("agent", {}) if isinstance(contract.get("agent"), dict) else {}
    authority = contract.get("authority", {}) if isinstance(contract.get("authority"), dict) else {}
    data = contract.get("data", {}) if isinstance(contract.get("data"), dict) else {}

    pkg = "aof." + _slug(agent.get("id", "agent")).replace("-", "_")
    prohibited = authority.get("prohibited_actions", []) or []
    permitted_sources = [
        s.get("source") for s in (data.get("permitted_sources", []) or [])
        if isinstance(s, dict) and s.get("source")
    ]
    decisions = [
        d for d in (authority.get("autonomous_decisions", []) or []) if isinstance(d, dict)
    ]

    out: List[str] = []
    out.append(f"# Rego policy STUB generated by aof from the AOF contract for "
               f"'{agent.get('id', 'agent')}'.")
    out.append("#")
    out.append("# AOF generates policy INPUTS; it does not enforce policy at runtime.")
    out.append("# This stub is a starting point for a runtime policy layer that YOU own,")
    out.append("# complete, test, and review. Every rule below is marked TODO.")
    out.append("")
    out.append(f"package {pkg}")
    out.append("")
    out.append("import rego.v1")
    out.append("")
    out.append("# Default deny — actions must be explicitly allowed by a completed rule.")
    out.append("default allow := false")
    out.append("")

    out.append("# --- Prohibited actions (hard limits from authority.prohibited_actions) ---")
    if prohibited:
        out.append("prohibited_actions := {")
        for p in prohibited:
            out.append(f"    {json.dumps(str(p))},")
        out.append("}")
    else:
        out.append("prohibited_actions := set()  # TODO: none declared in contract")
    out.append("")
    out.append("# TODO: map input.action to the human-readable prohibitions above.")
    out.append("deny contains msg if {")
    out.append("    some action in prohibited_actions")
    out.append("    input.action == action  # TODO: define how input.action is populated")
    out.append("    msg := sprintf(\"prohibited action: %v\", [action])")
    out.append("}")
    out.append("")

    out.append("# --- Autonomous decision limits (from authority.autonomous_decisions) ---")
    for d in decisions:
        dtype = d.get("decision_type", "decision")
        limit = d.get("limit")
        if limit is not None:
            out.append(f"# TODO review: '{dtype}' is autonomous up to {limit} {d.get('currency', '')}".rstrip())
            out.append(f"allow if {{")
            out.append(f"    input.decision_type == {json.dumps(dtype)}")
            out.append(f"    input.amount <= {json.dumps(limit)}  # TODO: confirm units/currency")
            out.append(f"}}")
        else:
            out.append(f"# TODO review: '{dtype}' is autonomous with no numeric limit declared")
            out.append(f"allow if {{ input.decision_type == {json.dumps(dtype)} }}  # TODO: add conditions")
        out.append("")

    out.append("# --- Permitted data sources (from data.permitted_sources) ---")
    if permitted_sources:
        out.append("permitted_sources := {")
        for s in permitted_sources:
            out.append(f"    {json.dumps(str(s))},")
        out.append("}")
        out.append("")
        out.append("deny contains msg if {")
        out.append("    not input.data_source in permitted_sources  # TODO: define input.data_source")
        out.append("    msg := sprintf(\"data source not permitted: %v\", [input.data_source])")
        out.append("}")
    else:
        out.append("permitted_sources := set()  # TODO: none declared in contract")
    out.append("")
    return "\n".join(out) + "\n"


def export(contract: Dict[str, Any], fmt: str) -> str:
    """Render ``contract`` in the requested format. Returns a string."""
    if fmt == "markdown":
        return to_markdown(contract)
    if fmt == "a2a-card":
        return json.dumps(to_a2a_card(contract), indent=2) + "\n"
    if fmt == "opa":
        return to_opa_rego(contract)
    raise ValueError(f"unknown export format: {fmt}")
