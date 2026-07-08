"""
aof — Agent Ownership Framework command-line interface.

Subcommands:
    aof validate <path> [path ...]   Validate contract(s) against the JSON Schema
    aof check <file>                 Check all eight governance boundaries
    aof create <name.yaml>           Create a new contract from the template
    aof export <file>                (stub) Export deployment-time policy artifacts

``<path>`` for ``validate`` may be a file, a directory (searched recursively for
``*.yaml`` / ``*.yml``), or a glob.

AOF performs deployment-time contract validation. It does not enforce policy at
runtime; any artifacts a future ``export`` command produces are inputs to a
separate runtime policy layer.

Author: Anitha Jagadeesh — Enterprise Data AI Realities
License: MIT
"""

import argparse
import os
import shutil
import sys
from typing import List

from . import __version__
from . import validator as V
from .boundaries import run_all_boundaries

RESET = V.RESET
BOLD = V.BOLD
DIM = "\033[2m" if V._supports_color() else ""
GREEN = V.GREEN
RED = V.RED
YELLOW = V.YELLOW


def _template_path() -> str:
    """Locate the blank contract template (repo layout when available)."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.environ.get("AOF_TEMPLATE_PATH", ""),
        os.path.normpath(os.path.join(here, "..", "..", "templates", "contract-template.yaml")),
        os.path.join(here, "templates", "contract-template.yaml"),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return candidates[1]  # best-effort default for the error message


# ---------------------------------------------------------------------------
# aof validate
# ---------------------------------------------------------------------------

def cmd_validate(args: argparse.Namespace) -> int:
    try:
        schema = V.load_schema()
    except FileNotFoundError as e:
        print(V.fail(f"Cannot load schema: {e}"), file=sys.stderr)
        return 1

    files = V.expand_paths(args.paths)

    if not files:
        msg = f"No contract files (*.yaml/*.yml) found in: {', '.join(args.paths)}"
        if args.strict:
            print(V.fail(msg), file=sys.stderr)
            return 1
        print(V.warn(msg))
        return 0

    results = []
    any_failed = False
    for filepath in files:
        passed, errors = V.validate_file(filepath, schema, verbose=args.verbose)
        if not passed:
            any_failed = True
        results.append({"file": filepath, "passed": passed, "errors": errors})
        if args.output == "text":
            V.print_result(filepath, passed, errors)

    total = len(results)
    failed = sum(1 for r in results if not r["passed"])
    if args.output == "json":
        print(V.format_json_output(results))
    else:
        print()
        if failed == 0:
            print(V.ok(f"All {total} contract(s) valid"))
        else:
            print(V.fail(f"{failed}/{total} contract(s) failed validation"))

    return 1 if any_failed else 0


# ---------------------------------------------------------------------------
# aof create
# ---------------------------------------------------------------------------

def cmd_create(args: argparse.Namespace) -> int:
    template = _template_path()
    if not os.path.exists(template):
        print(f"{RED}ERROR:{RESET} Template not found:\n  {template}", file=sys.stderr)
        return 1

    dest = args.name
    if os.path.exists(dest):
        print(
            f"{RED}ERROR:{RESET} '{dest}' already exists.\n"
            "Choose a different name or delete the existing file first.",
            file=sys.stderr,
        )
        return 1

    parent = os.path.dirname(dest)
    if parent:
        os.makedirs(parent, exist_ok=True)

    try:
        shutil.copy2(template, dest)
    except OSError as e:
        print(f"{RED}ERROR:{RESET} Could not create '{dest}': {e}", file=sys.stderr)
        return 1

    print(V.ok(f"Created: {BOLD}{dest}{RESET}"))
    print()
    print(f"{DIM}Next steps:{RESET}")
    print(f"  1. Open {BOLD}{dest}{RESET} and replace all placeholder values")
    print(f"  2. Validate the schema:      aof validate {dest}")
    print(f"  3. Check all 8 boundaries:   aof check {dest}")
    return 0


# ---------------------------------------------------------------------------
# aof check
# ---------------------------------------------------------------------------

def cmd_check(args: argparse.Namespace) -> int:
    try:
        import yaml
    except ImportError:
        print(f"{RED}ERROR:{RESET} pyyaml is required. Run: pip install pyyaml", file=sys.stderr)
        return 1

    filepath = args.file
    filename = os.path.basename(filepath)

    if not os.path.exists(filepath):
        print(f"{RED}ERROR:{RESET} File not found: {filepath}", file=sys.stderr)
        return 1

    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            contract = yaml.safe_load(fh)
    except yaml.YAMLError as e:
        print(f"{RED}ERROR:{RESET} YAML parse error in {filename}:\n  {e}", file=sys.stderr)
        return 1

    if not isinstance(contract, dict):
        print(f"{RED}ERROR:{RESET} {filename} is not a YAML mapping.", file=sys.stderr)
        return 1

    try:
        schema = V.load_schema()
    except FileNotFoundError as e:
        print(f"{RED}ERROR:{RESET} {e}", file=sys.stderr)
        return 1

    schema_passed, schema_errors = V.validate_file(filepath, schema)

    rule = "═" * 54
    div = "─" * 54
    print()
    print(f"{BOLD}Contract Boundary Check: {filename}{RESET}")
    print(rule)
    print()

    if schema_passed:
        print(f"  Schema validation:  {GREEN}✓ PASS{RESET}")
    else:
        print(f"  Schema validation:  {RED}✗ FAIL  ({len(schema_errors)} error(s)){RESET}")
        for err in schema_errors[:5]:
            print(f"    {RED}→{RESET} {err}")
        if len(schema_errors) > 5:
            print(f"    {DIM}... and {len(schema_errors) - 5} more.  Run: aof validate {filepath}{RESET}")
    print()

    boundaries = run_all_boundaries(contract)
    all_b_pass = all(b.passed for b in boundaries)

    for b in boundaries:
        status = f"{GREEN}✓{RESET}" if b.passed else f"{RED}✗{RESET}"
        print(f"  {status} Boundary {b.number} — {BOLD}{b.name}{RESET}")
        for item_ok, msg in b.items:
            icon = f"{GREEN}✓{RESET}" if item_ok else f"{RED}✗{RESET}"
            print(f"      {icon} {msg}")
        print()

    print(div)
    failed_b = sum(1 for b in boundaries if not b.passed)

    if schema_passed and all_b_pass:
        print(f"  {GREEN}✓ All 8 boundaries satisfied — contract is governance-complete{RESET}")
        return 0

    parts = []
    if not schema_passed:
        parts.append(f"{len(schema_errors)} schema error(s)")
    if failed_b:
        parts.append(f"{failed_b}/8 boundaries incomplete")
    print(f"  {RED}✗ {', '.join(parts)}{RESET}")
    if not schema_passed:
        print(f"  {DIM}Full error list: aof validate {filepath}{RESET}")
    return 1


# ---------------------------------------------------------------------------
# aof export  (Phase 3 stub)
# ---------------------------------------------------------------------------

def cmd_export(args: argparse.Namespace) -> int:
    """Stub for the Phase 3 exporter.

    Planned: derive deployment-time policy artifacts (e.g., an A2A Agent Card
    or an OPA/Rego policy skeleton) from a validated contract. These are inputs
    to a separate runtime policy layer — AOF itself does not enforce at runtime.
    """
    print(V.warn("`aof export` is not implemented yet — planned for a future release."))
    print(f"  {DIM}It will generate deployment-time policy artifacts from a validated")
    print(f"  contract (e.g., A2A Agent Card, OPA/Rego skeleton). AOF does not")
    print(f"  enforce policy at runtime; these artifacts feed a separate layer.{RESET}")
    return 2


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aof",
        description="AOF — Agent Ownership Framework CLI (deployment-time contract validation).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"aof {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    p_val = sub.add_parser("validate", help="Validate contract(s) against the AOF JSON Schema")
    p_val.add_argument("paths", nargs="+", metavar="PATH",
                       help="Contract file(s), directory, or glob to validate")
    p_val.add_argument("--strict", action="store_true",
                       help="Fail (non-zero) if no contracts are found")
    p_val.add_argument("--verbose", "-v", action="store_true",
                       help="Print each individual check result")
    p_val.add_argument("--output", choices=["text", "json"], default="text",
                       help="Output format (default: text)")
    p_val.set_defaults(func=cmd_validate)

    p_check = sub.add_parser("check", help="Check all eight governance boundaries")
    p_check.add_argument("file", metavar="FILE", help="YAML contract file to check")
    p_check.set_defaults(func=cmd_check)

    p_create = sub.add_parser("create", help="Create a new contract from the blank template")
    p_create.add_argument("name", metavar="NAME.yaml", help="Output filename")
    p_create.set_defaults(func=cmd_create)

    p_export = sub.add_parser("export", help="(stub) Export deployment-time policy artifacts")
    p_export.add_argument("file", metavar="FILE", nargs="?", help="Validated contract to export")
    p_export.add_argument("--format", dest="fmt", default=None,
                          help="Planned target format (e.g., a2a-agent-card, opa)")
    p_export.set_defaults(func=cmd_export)

    return parser


def main(argv: List[str] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
