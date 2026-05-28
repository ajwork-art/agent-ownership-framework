#!/usr/bin/env python3
"""
Agent Ownership Framework (AOF) — Contract Validator

Validates AOF v1 agent ownership contract YAML files against the JSON Schema
and performs additional semantic checks beyond what JSON Schema can enforce.

Usage:
    python validate-contract.py <file> [<file> ...]
    python validate-contract.py examples/*.yaml
    python validate-contract.py --verbose my-agent-contract.yaml
    python validate-contract.py --output json my-agent-contract.yaml

Exit codes:
    0 — all files valid
    1 — one or more files failed validation

Author: Anitha Jagadeesh — Enterprise Data AI Realities
License: MIT
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError
except ImportError:
    print("ERROR: jsonschema is required. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Color output helpers
# ---------------------------------------------------------------------------

def _supports_color() -> bool:
    """Return True if the terminal supports ANSI color codes."""
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

def load_schema() -> Dict[str, Any]:
    """Load the AOF v1 JSON Schema from the schema directory."""
    # Resolve schema path relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(
        script_dir, "..", "schema", "v1", "agent-ownership-contract.schema.json"
    )
    schema_path = os.path.normpath(schema_path)

    if not os.path.exists(schema_path):
        raise FileNotFoundError(
            f"Schema not found at: {schema_path}\n"
            "Make sure you are running from the repository root or tools/ directory."
        )

    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Additional semantic checks
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+$")


def check_email(value: str, field_path: str) -> Optional[str]:
    """Validate an email address field. Returns error string or None."""
    if not EMAIL_RE.match(value):
        return f"{field_path}: '{value}' is not a valid email address"
    return None


def semantic_checks(contract: Dict[str, Any]) -> List[str]:
    """
    Perform additional checks beyond JSON Schema validation.

    These checks catch common mistakes that schema validation cannot enforce,
    such as sequential escalation levels and valid email formats in optional
    fields that the JSON Schema format keyword does not always enforce.

    Returns a list of error message strings. Empty list means all checks passed.
    """
    errors: List[str] = []

    # ---- SLA checks --------------------------------------------------------
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

    # ---- Escalation path checks -------------------------------------------
    ownership = contract.get("ownership", {})
    escalation = ownership.get("escalation_path", [])
    if isinstance(escalation, list) and len(escalation) > 0:
        levels = []
        for i, entry in enumerate(escalation):
            if isinstance(entry, dict):
                level = entry.get("level")
                if level is not None:
                    levels.append(level)
                # Email check for escalation contacts
                email = entry.get("email")
                if email and isinstance(email, str):
                    err = check_email(email, f"ownership.escalation_path[{i}].email")
                    if err:
                        errors.append(err)

        # Levels must be sequential starting at 1
        if levels:
            expected = list(range(1, len(levels) + 1))
            if sorted(levels) != expected:
                errors.append(
                    f"ownership.escalation_path: levels {sorted(levels)} are not sequential "
                    f"starting at 1 — expected {expected}"
                )

    # ---- Incident contact email check -------------------------------------
    accountability = contract.get("accountability", {})
    if isinstance(accountability, dict):
        incident_contact = accountability.get("incident_contact")
        if incident_contact and isinstance(incident_contact, str):
            err = check_email(incident_contact, "accountability.incident_contact")
            if err:
                errors.append(err)

    # ---- Kill switch owner email check ------------------------------------
    risk = contract.get("risk", {})
    if isinstance(risk, dict):
        kill_switch_owner = risk.get("kill_switch_owner")
        if kill_switch_owner and isinstance(kill_switch_owner, str):
            err = check_email(kill_switch_owner, "risk.kill_switch_owner")
            if err:
                errors.append(err)

    # ---- Primary owner email check ----------------------------------------
    primary_owner = ownership.get("primary_owner", {})
    if isinstance(primary_owner, dict):
        email = primary_owner.get("email")
        if email and isinstance(email, str):
            err = check_email(email, "ownership.primary_owner.email")
            if err:
                errors.append(err)

    return errors


# ---------------------------------------------------------------------------
# Core validation function
# ---------------------------------------------------------------------------

def validate_file(
    filepath: str,
    schema: Dict[str, Any],
    verbose: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Validate a single YAML contract file.

    Args:
        filepath: Path to the YAML file.
        schema: Parsed JSON Schema dict.
        verbose: If True, print each check result.

    Returns:
        (passed: bool, errors: List[str])
    """
    errors: List[str] = []

    # 1. File existence check
    if not os.path.exists(filepath):
        return False, [f"File not found: {filepath}"]

    # 2. YAML parse check
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            contract = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, [f"YAML parse error: {e}"]

    if not isinstance(contract, dict):
        return False, ["File does not contain a YAML mapping (expected top-level object)"]

    if verbose:
        print(f"  {ok('YAML parsed successfully')}")

    # 3. JSON Schema validation
    validator = Draft7Validator(schema)
    schema_errors = sorted(validator.iter_errors(contract), key=lambda e: str(e.path))

    if schema_errors:
        for err in schema_errors:
            field_path = ".".join(str(p) for p in err.absolute_path) if err.absolute_path else "(root)"
            errors.append(f"Schema: [{field_path}] {err.message}")
    else:
        if verbose:
            print(f"  {ok('JSON Schema validation passed')}")

    # 4. Semantic checks
    semantic_errors = semantic_checks(contract)
    if semantic_errors:
        errors.extend([f"Semantic: {e}" for e in semantic_errors])
    else:
        if verbose:
            print(f"  {ok('Semantic checks passed')}")

    passed = len(errors) == 0
    return passed, errors


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def print_result(filepath: str, passed: bool, errors: List[str], verbose: bool) -> None:
    """Print colorized validation result for a single file."""
    filename = os.path.basename(filepath)
    if passed:
        print(ok(f"{BOLD}{filename}{RESET}"))
    else:
        print(fail(f"{BOLD}{filename}{RESET}"))
        for error in errors:
            print(f"    {RED}→{RESET} {error}")


def format_json_output(results: List[Dict]) -> str:
    """Format results as JSON for machine-readable output."""
    return json.dumps(
        {
            "aof_validator": "1.0.0",
            "total": len(results),
            "passed": sum(1 for r in results if r["passed"]),
            "failed": sum(1 for r in results if not r["passed"]),
            "results": results,
        },
        indent=2,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="validate-contract",
        description=(
            "AOF v1 Contract Validator — validates agent ownership contract YAML files "
            "against the AOF JSON Schema and performs additional semantic checks."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate-contract.py examples/support-agent.yaml
  python validate-contract.py examples/*.yaml
  python validate-contract.py --verbose examples/fraud-detection-agent.yaml
  python validate-contract.py --output json examples/support-agent.yaml
        """,
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more YAML contract files to validate",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Print each individual check result (pass/fail per check)",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json for machine-readable output",
    )
    return parser.parse_args()


def main() -> int:
    """
    Main entry point. Returns exit code: 0 on success, 1 on any failure.
    """
    args = parse_args()

    # Load schema once
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

        results.append(
            {
                "file": filepath,
                "passed": passed,
                "errors": errors,
            }
        )

        if args.output == "text":
            print_result(filepath, passed, errors, args.verbose)

    # Summary line
    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = total - passed_count

    if args.output == "text":
        print()
        if failed_count == 0:
            print(ok(f"All {total} contract(s) valid"))
        else:
            print(fail(f"{failed_count}/{total} contract(s) failed validation"))
    else:
        print(format_json_output(results))

    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
