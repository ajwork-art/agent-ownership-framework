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
import json
import os
import shutil
import sys
from typing import Any, Dict, List

from . import __version__
from . import validator as V
from .boundaries import run_all_boundaries
from . import diff as D
from . import exporters
from . import verify as gpgverify

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

def _print_result_text(result: Dict[str, Any], passed: bool, strict: bool) -> None:
    name = os.path.basename(result["file"])
    if passed:
        print(V.ok(f"{BOLD}{name}{RESET}"))
    else:
        print(V.fail(f"{BOLD}{name}{RESET}"))
    for e in result["errors"]:
        print(f"    {RED}→{RESET} {e}")
    strict_tag = f" {DIM}(fails under --strict){RESET}" if not strict else ""
    for w in result["warnings"]:
        print(f"    {YELLOW}!{RESET} {w}{strict_tag}")
    for n in result["notices"]:
        print(f"    {DIM}· {n}{RESET}")


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
        r = V.evaluate_file(filepath, schema)
        passed = V.result_passed(r, strict=args.strict)
        if not passed:
            any_failed = True
        results.append({
            "file": filepath,
            "passed": passed,
            "status": V.contract_status(r),
            "schema_version": V.schema_version_of(r["contract"]) if r["contract"] else None,
            "errors": r["errors"],
            "warnings": r["warnings"],
            "notices": r["notices"],
        })
        if args.output == "text":
            _print_result_text(r, passed, args.strict)

    total = len(results)
    failed = sum(1 for r in results if not r["passed"])
    warned = sum(1 for r in results if r["warnings"])

    if args.output == "json":
        print(json.dumps({
            "aof": __version__,
            "strict": args.strict,
            "total": total,
            "passed": total - failed,
            "failed": failed,
            "with_warnings": warned,
            "results": results,
        }, indent=2))
    else:
        print()
        if failed == 0:
            suffix = f" ({warned} with warnings)" if warned and not args.strict else ""
            print(V.ok(f"All {total} contract(s) valid{suffix}"))
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
# aof scan  (fleet inventory)
# ---------------------------------------------------------------------------

_STATUS_STYLE = {
    "valid": GREEN,
    "unsigned": YELLOW,
    "expired": YELLOW,
    "invalid": RED,
}


def cmd_scan(args: argparse.Namespace) -> int:
    try:
        schema = V.load_schema()
    except FileNotFoundError as e:
        print(V.fail(f"Cannot load schema: {e}"), file=sys.stderr)
        return 1

    files = V.expand_paths(args.paths)
    rows = []
    for filepath in files:
        r = V.evaluate_file(filepath, schema)
        contract = r["contract"] or {}
        owners = V.owners_summary(contract)
        agent = contract.get("agent", {}) if isinstance(contract.get("agent"), dict) else {}
        rows.append({
            "file": filepath,
            "agent_id": agent.get("id"),
            "status": V.contract_status(r),
            "signed": V.signoff_complete(contract),
            "domain_owner": owners["domain_owner"],
            "technical_owner": owners["technical_owner"],
            "schema_version": V.schema_version_of(contract) if r["contract"] else None,
            "warnings": r["warnings"],
            "errors": r["errors"],
        })

    counts = {s: sum(1 for row in rows if row["status"] == s)
              for s in ("valid", "unsigned", "expired", "invalid")}
    no_owner = sum(1 for row in rows if not row["domain_owner"])
    unsigned = sum(1 for row in rows if not row["signed"])
    summary = {
        "total": len(rows),
        "by_status": counts,
        "missing_domain_owner": no_owner,
        "unsigned": unsigned,
    }

    if args.json:
        print(json.dumps({"aof": __version__, "summary": summary, "contracts": rows}, indent=2))
        return 1 if counts["invalid"] else 0

    if not rows:
        print(V.warn(f"No contracts found under: {', '.join(args.paths)}"))
        return 0

    id_w = max([len(str(r["agent_id"] or "?")) for r in rows] + [8])
    own_w = max([len(str(r["domain_owner"] or "—")) for r in rows] + [12])
    print(f"{BOLD}{'AGENT':<{id_w}}  {'STATUS':<9}  {'SIGNED':<6}  {'DOMAIN OWNER':<{own_w}}{RESET}")
    print("─" * (id_w + own_w + 27))
    for r in rows:
        style = _STATUS_STYLE.get(r["status"], "")
        signed = "yes" if r["signed"] else "NO"
        print(f"{str(r['agent_id'] or '?'):<{id_w}}  "
              f"{style}{r['status']:<9}{RESET}  {signed:<6}  {str(r['domain_owner'] or '—'):<{own_w}}")

    print()
    print(f"{BOLD}Fleet summary:{RESET} {summary['total']} contract(s) — "
          f"{GREEN}{counts['valid']} valid{RESET}, "
          f"{YELLOW}{counts['unsigned']} unsigned{RESET}, "
          f"{YELLOW}{counts['expired']} expired{RESET}, "
          f"{RED}{counts['invalid']} invalid{RESET}")
    print(f"  {no_owner} without a named domain owner · {unsigned} without complete sign-off")
    return 1 if counts["invalid"] else 0


# ---------------------------------------------------------------------------
# aof diff  (semantic diff)
# ---------------------------------------------------------------------------

def _load_yaml(path: str):
    import yaml
    if not os.path.exists(path):
        print(f"{RED}ERROR:{RESET} File not found: {path}", file=sys.stderr)
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as e:
        print(f"{RED}ERROR:{RESET} YAML parse error in {path}:\n  {e}", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        print(f"{RED}ERROR:{RESET} {path} is not a YAML mapping.", file=sys.stderr)
        return None
    return data


def cmd_diff(args: argparse.Namespace) -> int:
    old = _load_yaml(args.old)
    new = _load_yaml(args.new)
    if old is None or new is None:
        return 1

    result = D.diff_contracts(old, new)
    material = result["material"]
    cosmetic = result["cosmetic"]

    if args.json:
        print(json.dumps({
            "material": material,
            "cosmetic": cosmetic,
            "signoff_changed": result["signoff_changed"],
        }, indent=2))
    else:
        print(f"{BOLD}Semantic diff: {os.path.basename(args.old)} → {os.path.basename(args.new)}{RESET}")
        print()
        if not material and not cosmetic:
            print(V.ok("No differences."))
        else:
            print(f"{BOLD}Material changes ({len(material)}){RESET} "
                  f"{DIM}(authority · data · escalation · signoff){RESET}")
            for c in material:
                print(f"  {RED}◆{RESET} {c['path']} [{c['change']}]")
            print()
            print(f"{BOLD}Cosmetic changes ({len(cosmetic)}){RESET}")
            for c in cosmetic:
                print(f"  {DIM}◇ {c['path']} [{c['change']}]{RESET}")
        print()

    if material and args.require_reapproval and not result["signoff_changed"]:
        print(V.fail("Material changes present but the signoff block is unchanged — "
                     "re-approval required."), file=sys.stderr)
        return 1
    return 0


# ---------------------------------------------------------------------------
# aof verify  (optional detached-signature verification)
# ---------------------------------------------------------------------------

def cmd_verify(args: argparse.Namespace) -> int:
    contract_path = args.file
    signature_path = args.signature or gpgverify.default_signature_path(contract_path)

    if not signature_path:
        print(V.warn(
            f"No signature file found for {os.path.basename(contract_path)} "
            "(looked for .asc/.sig/.gpg). Pass --signature to specify one."))
        print(f"  {DIM}Signature verification is optional. Sign out of band with:")
        print(f"    gpg --armor --detach-sign {contract_path}{RESET}")
        return 1

    ok_sig, message = gpgverify.verify_gpg(contract_path, signature_path)
    if ok_sig:
        print(V.ok(f"Signature verified for {os.path.basename(contract_path)}"))
        print(f"  {DIM}{message}{RESET}")
        return 0
    print(V.fail(f"Signature NOT verified for {os.path.basename(contract_path)}"))
    print(f"  {DIM}{message}{RESET}")
    return 1


# ---------------------------------------------------------------------------
# aof export
# ---------------------------------------------------------------------------

def cmd_export(args: argparse.Namespace) -> int:
    if not args.file:
        print(f"{RED}ERROR:{RESET} a contract file is required: aof export --format "
              f"{args.fmt or 'markdown'} <file>", file=sys.stderr)
        return 1

    contract = _load_yaml(args.file)
    if contract is None:
        return 1

    try:
        rendered = exporters.export(contract, args.fmt)
    except ValueError as e:
        print(f"{RED}ERROR:{RESET} {e}", file=sys.stderr)
        return 1

    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as fh:
            fh.write(rendered)
        print(V.ok(f"Wrote {args.fmt} export to {args.output_file}"), file=sys.stderr)
    else:
        sys.stdout.write(rendered)
    return 0


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

    p_scan = sub.add_parser("scan", help="Fleet inventory of every contract under a directory")
    p_scan.add_argument("paths", nargs="+", metavar="PATH",
                        help="Directory/directories (or files/globs) to scan")
    p_scan.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    p_scan.set_defaults(func=cmd_scan)

    p_diff = sub.add_parser("diff", help="Semantic diff of two contract versions")
    p_diff.add_argument("old", metavar="OLD", help="Previous contract file")
    p_diff.add_argument("new", metavar="NEW", help="New contract file")
    p_diff.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    p_diff.add_argument("--require-reapproval", action="store_true",
                        help="Exit non-zero when material changes exist but signoff is unchanged")
    p_diff.set_defaults(func=cmd_diff)

    p_verify = sub.add_parser("verify", help="Verify an optional detached GPG signature")
    p_verify.add_argument("file", metavar="FILE", help="Contract file to verify")
    p_verify.add_argument("--signature", metavar="SIG",
                          help="Detached signature file (default: <file>.asc/.sig/.gpg)")
    p_verify.set_defaults(func=cmd_verify)

    p_export = sub.add_parser("export", help="Export a policy input / documentation artifact")
    p_export.add_argument("file", metavar="FILE", help="Validated contract to export")
    p_export.add_argument("--format", dest="fmt", required=True,
                          choices=["markdown", "a2a-card", "opa"],
                          help="markdown | a2a-card (experimental) | opa")
    p_export.add_argument("-o", "--output", dest="output_file", default=None,
                          help="Write to a file instead of stdout")
    p_export.set_defaults(func=cmd_export)

    return parser


def main(argv: List[str] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
