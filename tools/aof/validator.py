"""
Core validation logic for the Agent Ownership Framework (AOF).

This module is the single source of truth for schema loading, contract
validation, and the additional semantic checks. It is consumed by the ``aof``
CLI (``aof.cli``) and by the deprecated standalone ``validate-contract.py``
shim.

Author: Anitha Jagadeesh — Enterprise Data AI Realities
License: MIT
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only when dep missing
    print("ERROR: pyyaml is required. Install with: pip install pyyaml", file=sys.stderr)
    raise

try:
    from jsonschema import Draft7Validator
except ImportError:  # pragma: no cover - exercised only when dep missing
    print("ERROR: jsonschema is required. Install with: pip install jsonschema", file=sys.stderr)
    raise


# ---------------------------------------------------------------------------
# Color output helpers
# ---------------------------------------------------------------------------

def _supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


RESET = "\033[0m" if _supports_color() else ""
GREEN = "\033[92m" if _supports_color() else ""
RED = "\033[91m" if _supports_color() else ""
YELLOW = "\033[93m" if _supports_color() else ""
BOLD = "\033[1m" if _supports_color() else ""


def ok(msg: str) -> str:
    return f"{GREEN}✓{RESET} {msg}"


def fail(msg: str) -> str:
    return f"{RED}✗{RESET} {msg}"


def warn(msg: str) -> str:
    return f"{YELLOW}!{RESET} {msg}"


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))


def schema_candidate_paths() -> List[str]:
    """Ordered list of candidate locations for the AOF JSON Schema.

    1. ``AOF_SCHEMA_PATH`` environment override.
    2. The canonical repository copy (``schema/v1/...``) — used during local
       development and in CI, so the tooling always validates against the
       source-of-truth schema.
    3. The copy bundled inside the installed package (``aof/schema/...``) —
       used when the package is pip-installed away from the repository. A test
       asserts this copy is byte-identical to the canonical one.
    """
    paths: List[str] = []
    env = os.environ.get("AOF_SCHEMA_PATH")
    if env:
        paths.append(env)
    paths.append(
        os.path.normpath(
            os.path.join(
                _PACKAGE_DIR, "..", "..", "schema", "v1",
                "agent-ownership-contract.schema.json",
            )
        )
    )
    paths.append(
        os.path.join(_PACKAGE_DIR, "schema", "agent-ownership-contract.schema.json")
    )
    return paths


def load_schema() -> Dict[str, Any]:
    """Load the AOF JSON Schema from the first available candidate path."""
    for path in schema_candidate_paths():
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError(
        "AOF JSON Schema not found. Looked in:\n  "
        + "\n  ".join(p for p in schema_candidate_paths() if p)
        + "\nSet AOF_SCHEMA_PATH to point at agent-ownership-contract.schema.json."
    )


# ---------------------------------------------------------------------------
# Additional semantic checks
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+$")


def check_email(value: str, field_path: str) -> Optional[str]:
    if not EMAIL_RE.match(value):
        return f"{field_path}: '{value}' is not a valid email address"
    return None


def semantic_checks(contract: Dict[str, Any]) -> List[str]:
    """Checks beyond JSON Schema: SLA ranges, escalation ordering, emails."""
    errors: List[str] = []

    sla = contract.get("sla", {})
    if isinstance(sla, dict):
        availability = sla.get("availability")
        if availability is not None:
            if not isinstance(availability, (int, float)):
                errors.append("sla.availability: must be a number (e.g., 99.9), not a string")
            elif not (0 <= availability <= 100):
                errors.append(f"sla.availability: {availability} is out of range — must be 0 to 100")

        max_latency = sla.get("max_latency_ms")
        if max_latency is not None:
            if not isinstance(max_latency, int):
                errors.append("sla.max_latency_ms: must be an integer")
            elif max_latency < 1:
                errors.append(f"sla.max_latency_ms: {max_latency} must be >= 1")

    ownership = contract.get("ownership", {})
    escalation = ownership.get("escalation_path", [])
    if isinstance(escalation, list) and len(escalation) > 0:
        levels = []
        for i, entry in enumerate(escalation):
            if isinstance(entry, dict):
                level = entry.get("level")
                if level is not None:
                    levels.append(level)
                email = entry.get("email")
                if email and isinstance(email, str):
                    err = check_email(email, f"ownership.escalation_path[{i}].email")
                    if err:
                        errors.append(err)

        if levels:
            expected = list(range(1, len(levels) + 1))
            if sorted(levels) != expected:
                errors.append(
                    f"ownership.escalation_path: levels {sorted(levels)} are not sequential "
                    f"starting at 1 — expected {expected}"
                )

    risk = contract.get("risk", {})
    if isinstance(risk, dict):
        kill_switch_owner = risk.get("kill_switch_owner")
        if kill_switch_owner and isinstance(kill_switch_owner, str):
            err = check_email(kill_switch_owner, "risk.kill_switch_owner")
            if err:
                errors.append(err)

    return errors


# ---------------------------------------------------------------------------
# schema_version (v2, additive) and lifecycle enforcement
# ---------------------------------------------------------------------------

DEFAULT_SCHEMA_VERSION = "1.0"


def schema_version_of(contract: Dict[str, Any]) -> str:
    """Return the declared schema_version, defaulting to 1.0 when absent."""
    value = contract.get("schema_version")
    return value if isinstance(value, str) and value else DEFAULT_SCHEMA_VERSION


def schema_version_notice(contract: Dict[str, Any]) -> Optional[str]:
    """Informational (never an error) notice for contracts without schema_version.

    Backward compatibility: a valid v1 contract must still validate under v2.
    """
    if not contract.get("schema_version"):
        return (
            f"schema_version not declared — assuming {DEFAULT_SCHEMA_VERSION} (v1). "
            "All v2 fields are optional; this contract is valid."
        )
    return None


def _parse_iso_date(value: Any) -> Optional[date]:
    """Parse an ISO 8601 (YYYY-MM-DD) date string, or return None."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def lifecycle_checks(contract: Dict[str, Any], today: Optional[date] = None) -> List[str]:
    """Flag contracts whose lifecycle/governance dates have passed.

    Returns a list of warning strings. Warnings never fail validation on their
    own; ``aof validate --strict`` promotes them to failures (CI-blocking).
    Only explicit date fields are evaluated (no cadence arithmetic).
    """
    if today is None:
        today = date.today()

    warnings: List[str] = []
    status = None
    lifecycle = contract.get("lifecycle", {})
    if isinstance(lifecycle, dict):
        status = lifecycle.get("status")

    def _overdue(value: Any, label: str, message: str) -> None:
        d = _parse_iso_date(value)
        if d is not None and d < today:
            warnings.append(f"{label} {d.isoformat()} {message}")

    governance = contract.get("governance", {})
    if isinstance(governance, dict):
        _overdue(governance.get("next_review"), "governance.next_review",
                 "is in the past — governance review overdue")

    if isinstance(lifecycle, dict):
        if status != "retired":
            _overdue(lifecycle.get("retirement_date"), "lifecycle.retirement_date",
                     f"has passed but status is '{status}' — agent should be retired")
        retirement = lifecycle.get("retirement", {})
        if isinstance(retirement, dict):
            if status != "retired":
                _overdue(retirement.get("sunset_date"), "lifecycle.retirement.sunset_date",
                         f"has passed but status is '{status}' — agent should be retired")
            _overdue(retirement.get("planned_review_date"),
                     "lifecycle.retirement.planned_review_date",
                     "has passed — retirement decision review overdue")

    return warnings


# ---------------------------------------------------------------------------
# Core validation
# ---------------------------------------------------------------------------

def evaluate_file(
    filepath: str,
    schema: Dict[str, Any],
    today: Optional[date] = None,
) -> Dict[str, Any]:
    """Validate a contract file and gather errors, warnings, notices, and the
    parsed contract in a single pass.

    Returns a dict with keys: ``file``, ``errors`` (schema + semantic — always
    fail), ``warnings`` (lifecycle — fail only under ``--strict``), ``notices``
    (informational, never fail), and ``contract`` (parsed mapping or None).
    """
    result: Dict[str, Any] = {
        "file": filepath,
        "errors": [],
        "warnings": [],
        "notices": [],
        "contract": None,
    }

    if not os.path.exists(filepath):
        result["errors"].append(f"File not found: {filepath}")
        return result

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            contract = yaml.safe_load(f)
    except yaml.YAMLError as e:
        result["errors"].append(f"YAML parse error: {e}")
        return result

    if not isinstance(contract, dict):
        result["errors"].append("File does not contain a YAML mapping (expected top-level object)")
        return result

    result["contract"] = contract

    validator = Draft7Validator(schema)
    for err in sorted(validator.iter_errors(contract), key=lambda e: str(e.path)):
        field_path = ".".join(str(p) for p in err.absolute_path) if err.absolute_path else "(root)"
        result["errors"].append(f"Schema: [{field_path}] {err.message}")

    result["errors"].extend(f"Semantic: {e}" for e in semantic_checks(contract))
    result["warnings"].extend(lifecycle_checks(contract, today))
    notice = schema_version_notice(contract)
    if notice:
        result["notices"].append(notice)

    return result


def result_passed(result: Dict[str, Any], strict: bool = False) -> bool:
    """A result passes if it has no errors (and, under strict, no warnings)."""
    if result["errors"]:
        return False
    if strict and result["warnings"]:
        return False
    return True


# ---------------------------------------------------------------------------
# Inventory helpers (used by `aof scan`)
# ---------------------------------------------------------------------------

def signoff_complete(contract: Dict[str, Any]) -> bool:
    """True if both the domain and technical owners have signed the contract."""
    signoff = contract.get("signoff", {})
    if not isinstance(signoff, dict):
        return False
    for role in ("domain_owner", "technical_owner"):
        entry = signoff.get(role, {})
        if not isinstance(entry, dict) or not str(entry.get("name", "")).strip():
            return False
    return True


def owners_summary(contract: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Extract the named domain/technical owners for inventory reporting."""
    ownership = contract.get("ownership", {})
    ownership = ownership if isinstance(ownership, dict) else {}

    def _owner(key: str) -> Optional[str]:
        owner = ownership.get(key, {})
        if isinstance(owner, dict):
            name = str(owner.get("name", "")).strip()
            email = str(owner.get("email", "")).strip()
            if name and email:
                return f"{name} <{email}>"
            if name:
                return name
        return None

    return {
        "domain_owner": _owner("domain_owner"),
        "technical_owner": _owner("technical_owner"),
    }


def contract_status(result: Dict[str, Any]) -> str:
    """Classify a contract for fleet inventory.

    One of: 'invalid' (schema/semantic errors), 'expired' (lifecycle dates
    overdue), 'unsigned' (missing domain/technical signoff), or 'valid'.
    Precedence: invalid > expired > unsigned > valid.
    """
    if result["errors"]:
        return "invalid"
    contract = result.get("contract") or {}
    if result["warnings"]:
        return "expired"
    if not signoff_complete(contract):
        return "unsigned"
    return "valid"


def validate_file(
    filepath: str,
    schema: Dict[str, Any],
    verbose: bool = False,
) -> Tuple[bool, List[str]]:
    """Validate a single YAML contract file. Returns (passed, errors).

    Errors are schema + semantic only; lifecycle warnings never fail this call
    (use ``evaluate_file`` for warnings/notices). Kept stable for callers that
    predate v2.
    """
    result = evaluate_file(filepath, schema)
    errors = result["errors"]
    if verbose and not errors:
        print(f"  {ok('YAML parsed, schema and semantic checks passed')}")
    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Path expansion — accept files, directories, and globs
# ---------------------------------------------------------------------------

_YAML_EXTS = (".yaml", ".yml")


def expand_paths(paths: List[str]) -> List[str]:
    """Expand a list of files/directories/globs into contract file paths.

    - A directory expands to every ``*.yaml`` / ``*.yml`` beneath it (recursive).
    - A glob pattern expands via ``glob.glob``.
    - A plain path is used as-is.
    Results are de-duplicated and sorted for stable output.
    """
    import glob as _glob

    collected: List[str] = []
    for raw in paths:
        if os.path.isdir(raw):
            for root, _dirs, files in os.walk(raw):
                for name in files:
                    if name.lower().endswith(_YAML_EXTS):
                        collected.append(os.path.join(root, name))
        elif any(ch in raw for ch in "*?["):
            collected.extend(_glob.glob(raw, recursive=True))
        else:
            collected.append(raw)

    seen = set()
    unique: List[str] = []
    for p in sorted(collected):
        norm = os.path.normpath(p)
        if norm not in seen:
            seen.add(norm)
            unique.append(p)
    return unique


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def format_json_output(results: List[Dict]) -> str:
    return json.dumps(
        {
            "aof_validator": "2.0.0",
            "total": len(results),
            "passed": sum(1 for r in results if r["passed"]),
            "failed": sum(1 for r in results if not r["passed"]),
            "results": results,
        },
        indent=2,
    )


def print_result(filepath: str, passed: bool, errors: List[str]) -> None:
    filename = os.path.basename(filepath)
    if passed:
        print(ok(f"{BOLD}{filename}{RESET}"))
    else:
        print(fail(f"{BOLD}{filename}{RESET}"))
        for error in errors:
            print(f"    {RED}→{RESET} {error}")


# ---------------------------------------------------------------------------
# Legacy standalone CLI (preserved for validate-contract.py)
# ---------------------------------------------------------------------------

def run_standalone(argv: Optional[List[str]] = None) -> int:
    """Reproduce the historical ``validate-contract.py`` command-line interface.

    Kept so the deprecated standalone script behaves exactly as before,
    including ``--verbose`` and ``--output json``.
    """
    parser = argparse.ArgumentParser(
        prog="validate-contract",
        description="AOF Contract Validator (legacy standalone interface).",
    )
    parser.add_argument("files", nargs="+", metavar="FILE")
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    try:
        schema = load_schema()
    except FileNotFoundError as e:
        print(fail(f"Cannot load schema: {e}"), file=sys.stderr)
        return 1

    results = []
    any_failed = False
    for filepath in args.files:
        if args.output == "text" and args.verbose:
            print(f"\n{BOLD}Validating: {filepath}{RESET}")
        passed, errors = validate_file(filepath, schema, verbose=args.verbose)
        if not passed:
            any_failed = True
        results.append({"file": filepath, "passed": passed, "errors": errors})
        if args.output == "text":
            print_result(filepath, passed, errors)

    total = len(results)
    failed_count = sum(1 for r in results if not r["passed"])
    if args.output == "text":
        print()
        if failed_count == 0:
            print(ok(f"All {total} contract(s) valid"))
        else:
            print(fail(f"{failed_count}/{total} contract(s) failed validation"))
    else:
        print(format_json_output(results))

    return 1 if any_failed else 0
