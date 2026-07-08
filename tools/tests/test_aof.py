"""Tests for the aof package: validation, boundaries, CLI, and schema parity."""

import filecmp
import json
import os
import subprocess
import sys

import pytest

# Make the package importable when running from a checkout (tools/ on path).
TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, TOOLS_DIR)

from aof import validator as V  # noqa: E402
from aof.boundaries import run_all_boundaries  # noqa: E402
from aof.cli import main as cli_main  # noqa: E402

EXAMPLES_DIR = os.path.join(REPO_ROOT, "examples")
EXAMPLE_FILES = sorted(
    os.path.join(EXAMPLES_DIR, f)
    for f in os.listdir(EXAMPLES_DIR)
    if f.endswith(".yaml")
)


@pytest.fixture(scope="module")
def schema():
    return V.load_schema()


def test_examples_discovered():
    assert EXAMPLE_FILES, "no example contracts found"


@pytest.mark.parametrize("path", EXAMPLE_FILES, ids=os.path.basename)
def test_examples_validate(path, schema):
    passed, errors = V.validate_file(path, schema)
    assert passed, f"{os.path.basename(path)} failed: {errors}"


@pytest.mark.parametrize("path", EXAMPLE_FILES, ids=os.path.basename)
def test_examples_pass_all_boundaries(path):
    import yaml
    with open(path, encoding="utf-8") as fh:
        contract = yaml.safe_load(fh)
    boundaries = run_all_boundaries(contract)
    incomplete = [b.name for b in boundaries if not b.passed]
    assert not incomplete, f"{os.path.basename(path)} incomplete boundaries: {incomplete}"


def test_invalid_contract_fails(tmp_path, schema):
    bad = tmp_path / "bad.yaml"
    bad.write_text("apiVersion: aof/v1\nkind: AgentOwnershipContract\n")  # missing required sections
    passed, errors = V.validate_file(str(bad), schema)
    assert not passed
    assert errors


def test_semantic_checks_catch_bad_sla():
    contract = {"sla": {"availability": 150, "max_latency_ms": 0}}
    errors = V.semantic_checks(contract)
    assert any("availability" in e for e in errors)
    assert any("max_latency_ms" in e for e in errors)


def test_semantic_checks_catch_nonsequential_escalation():
    contract = {"ownership": {"escalation_path": [{"level": 1}, {"level": 3}]}}
    errors = V.semantic_checks(contract)
    assert any("sequential" in e for e in errors)


def test_expand_paths_directory():
    files = V.expand_paths([EXAMPLES_DIR])
    assert len(files) == len(EXAMPLE_FILES)
    assert all(f.endswith((".yaml", ".yml")) for f in files)


def test_bundled_schema_matches_canonical():
    """The schema bundled in the package must stay identical to schema/v1/."""
    canonical = os.path.join(
        REPO_ROOT, "schema", "v1", "agent-ownership-contract.schema.json"
    )
    bundled = os.path.join(
        TOOLS_DIR, "aof", "schema", "agent-ownership-contract.schema.json"
    )
    assert filecmp.cmp(canonical, bundled, shallow=False), (
        "Bundled schema has drifted from schema/v1/. "
        "Re-copy: cp schema/v1/agent-ownership-contract.schema.json "
        "tools/aof/schema/agent-ownership-contract.schema.json"
    )


def test_cli_validate_directory_ok(capsys):
    rc = cli_main(["validate", EXAMPLES_DIR])
    assert rc == 0


def test_cli_validate_strict_no_files(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    assert cli_main(["validate", "--strict", str(empty)]) == 1
    assert cli_main(["validate", str(empty)]) == 0  # non-strict: warning only


def test_cli_validate_json_output(capsys):
    rc = cli_main(["validate", "--output", "json", EXAMPLE_FILES[0]])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["total"] == 1
    assert payload["passed"] == 1
    assert rc == 0


def test_standalone_shim_runs():
    """The deprecated validate-contract.py must still validate a good contract."""
    script = os.path.join(TOOLS_DIR, "validate-contract.py")
    result = subprocess.run(
        [sys.executable, script, EXAMPLE_FILES[0]],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "deprecated" in result.stderr.lower()
