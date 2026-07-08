"""Tests for Phase 3 v2 capabilities: lifecycle, scan, diff, verify, export."""

import copy
import json
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest
import yaml

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, TOOLS_DIR)

from aof import validator as V  # noqa: E402
from aof.diff import diff_contracts  # noqa: E402
from aof import exporters  # noqa: E402
from aof import verify as gpgverify  # noqa: E402
from aof.cli import main as cli_main  # noqa: E402

SUPPORT = os.path.join(REPO_ROOT, "examples", "support-agent.yaml")


@pytest.fixture(scope="module")
def schema():
    return V.load_schema()


@pytest.fixture(scope="module")
def contract():
    with open(SUPPORT, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# --- schema_version --------------------------------------------------------

def test_schema_version_defaults_to_1_0(contract):
    assert V.schema_version_of(contract) == "1.0"
    assert V.schema_version_notice(contract) is not None


def test_declared_schema_version(contract):
    c = copy.deepcopy(contract)
    c["schema_version"] = "2.0"
    assert V.schema_version_of(c) == "2.0"
    assert V.schema_version_notice(c) is None


def test_v2_contract_validates(tmp_path, schema, contract):
    c = copy.deepcopy(contract)
    c["schema_version"] = "2.0"
    p = tmp_path / "v2.yaml"
    p.write_text(yaml.safe_dump(c))
    passed, errors = V.validate_file(str(p), schema)
    assert passed, errors


def test_v1_contract_still_validates_with_notice(tmp_path, schema, contract):
    p = tmp_path / "v1.yaml"
    p.write_text(yaml.safe_dump(contract))
    result = V.evaluate_file(str(p), schema)
    assert not result["errors"]
    assert any("schema_version" in n for n in result["notices"])


# --- lifecycle enforcement -------------------------------------------------

def test_lifecycle_flags_past_next_review(contract):
    c = copy.deepcopy(contract)
    c["governance"]["next_review"] = "2020-01-01"
    warnings = V.lifecycle_checks(c, today=date(2026, 7, 8))
    assert any("next_review" in w for w in warnings)


def test_lifecycle_flags_past_sunset_unless_retired(contract):
    c = copy.deepcopy(contract)
    c["lifecycle"].setdefault("retirement", {})["sunset_date"] = "2020-01-01"
    assert V.lifecycle_checks(c, today=date(2026, 7, 8))
    c["lifecycle"]["status"] = "retired"
    assert not any("sunset_date" in w for w in V.lifecycle_checks(c, today=date(2026, 7, 8)))


def test_strict_promotes_warnings_to_failure(tmp_path, schema, contract):
    c = copy.deepcopy(contract)
    c["governance"]["next_review"] = "2020-01-01"
    p = tmp_path / "expired.yaml"
    p.write_text(yaml.safe_dump(c))
    result = V.evaluate_file(str(p), schema)
    assert V.result_passed(result, strict=False) is True
    assert V.result_passed(result, strict=True) is False


def test_cli_validate_strict_expired_exits_1(tmp_path, contract):
    c = copy.deepcopy(contract)
    c["governance"]["next_review"] = "2020-01-01"
    p = tmp_path / "expired.yaml"
    p.write_text(yaml.safe_dump(c))
    assert cli_main(["validate", str(p)]) == 0            # non-strict: warning only
    assert cli_main(["validate", "--strict", str(p)]) == 1  # strict: blocking


# --- inventory / scan ------------------------------------------------------

def test_contract_status_and_signoff(tmp_path, schema, contract):
    # unsigned but schema-valid: signoff present with blank names (schema requires
    # the signoff block, so a *missing* one is 'invalid', not 'unsigned').
    unsigned = copy.deepcopy(contract)
    unsigned["signoff"]["domain_owner"]["name"] = ""
    unsigned["signoff"]["technical_owner"]["name"] = ""
    up = tmp_path / "unsigned.yaml"
    up.write_text(yaml.safe_dump(unsigned))
    assert V.contract_status(V.evaluate_file(str(up), schema)) == "unsigned"

    # missing signoff block entirely -> schema invalid
    invalid = copy.deepcopy(contract)
    invalid.pop("signoff", None)
    ip = tmp_path / "invalid.yaml"
    ip.write_text(yaml.safe_dump(invalid))
    assert V.contract_status(V.evaluate_file(str(ip), schema)) == "invalid"

    # expired
    expired = copy.deepcopy(contract)
    expired["governance"]["next_review"] = "2020-01-01"
    ep = tmp_path / "expired.yaml"
    ep.write_text(yaml.safe_dump(expired))
    assert V.contract_status(V.evaluate_file(str(ep), schema)) == "expired"

    # valid
    assert V.contract_status(V.evaluate_file(SUPPORT, schema)) == "valid"
    assert V.signoff_complete(contract) is True


def test_owners_summary(contract):
    owners = V.owners_summary(contract)
    assert owners["domain_owner"] and "@" in owners["domain_owner"]
    assert owners["technical_owner"]


def test_cli_scan_json(capsys):
    examples_dir = os.path.join(REPO_ROOT, "examples")
    expected = len([f for f in os.listdir(examples_dir) if f.endswith((".yaml", ".yml"))])
    rc = cli_main(["scan", "--json", examples_dir])
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["total"] == expected
    assert rc == 0


# --- semantic diff ---------------------------------------------------------

def test_diff_material_vs_cosmetic(contract):
    old = copy.deepcopy(contract)
    new = copy.deepcopy(contract)
    new["metadata"]["updated"] = "2099-01-01"            # cosmetic
    new["authority"]["prohibited_actions"].append("Cannot X")  # material
    result = diff_contracts(old, new)
    mat = [c["path"] for c in result["material"]]
    cos = [c["path"] for c in result["cosmetic"]]
    assert any(p.startswith("authority.prohibited_actions") for p in mat)
    assert any(p.startswith("metadata.updated") for p in cos)


def test_diff_signoff_change_detected(contract):
    old = copy.deepcopy(contract)
    new = copy.deepcopy(contract)
    new["signoff"]["domain_owner"]["date"] = "2099-01-01"
    result = diff_contracts(old, new)
    assert result["signoff_changed"] is True


def test_cli_diff_require_reapproval(tmp_path, contract):
    base = tmp_path / "base.yaml"
    changed = tmp_path / "changed.yaml"
    base.write_text(yaml.safe_dump(contract))
    c2 = copy.deepcopy(contract)
    c2["data"]["prohibited_sources"].append("A new prohibited source")  # material
    changed.write_text(yaml.safe_dump(c2))
    # material change, signoff unchanged -> non-zero
    assert cli_main(["diff", "--require-reapproval", str(base), str(changed)]) == 1
    # same file -> zero
    assert cli_main(["diff", "--require-reapproval", str(base), str(base)]) == 0


# --- exporters -------------------------------------------------------------

def test_export_markdown(contract):
    md = exporters.to_markdown(contract)
    assert md.startswith("# Ownership Card")
    assert "does not enforce" in md
    assert "Sarah Chen" in md


def test_export_markdown_escalation_uses_numeric_levels(contract):
    # support-agent escalation_path: level 1 David Park, level 2 Lisa Torres.
    md = exporters.to_markdown(contract)
    assert "1. David Park" in md
    assert "2. Lisa Torres" in md
    # no repeated "1." for the second entry
    assert "1. Lisa Torres" not in md


def test_export_a2a_card_experimental(contract):
    card = exporters.to_a2a_card(contract)
    assert card["protocolVersion"] == "1.0.0"
    assert card["x-aof"]["experimental"] is True
    assert "a2a-protocol.org" in card["x-aof"]["a2a_spec"]
    assert len(card["skills"]) >= 1
    assert all({"id", "name", "description"} <= set(s) for s in card["skills"])


def test_export_opa_stub(contract):
    rego = exporters.to_opa_rego(contract)
    assert rego.startswith("#")
    assert "package aof." in rego
    assert "TODO" in rego
    assert "does not enforce" in rego


def test_cli_export_to_file(tmp_path):
    out = tmp_path / "card.md"
    rc = cli_main(["export", "--format", "markdown", "-o", str(out), SUPPORT])
    assert rc == 0
    assert out.read_text().startswith("# Ownership Card")


# --- verify (optional GPG) -------------------------------------------------

def test_verify_no_signature_returns_1(tmp_path, contract):
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(contract))
    assert cli_main(["verify", str(p)]) == 1  # no signature present


@pytest.mark.skipif(not gpgverify.gpg_available(), reason="gpg not installed")
def test_verify_gpg_roundtrip(tmp_path, contract):
    gnupghome = tmp_path / "gnupg"
    gnupghome.mkdir(mode=0o700)
    env = dict(os.environ, GNUPGHOME=str(gnupghome))

    # Generate a throwaway, passphrase-less key in the isolated keyring.
    batch = tmp_path / "keyparams"
    batch.write_text(
        "%no-protection\nKey-Type: RSA\nKey-Length: 2048\n"
        "Name-Real: AOF Test\nName-Email: aof-test@example.com\n"
        "Expire-Date: 0\n%commit\n"
    )
    gen = subprocess.run(["gpg", "--batch", "--generate-key", str(batch)],
                         env=env, capture_output=True, text=True)
    if gen.returncode != 0:
        pytest.skip(f"could not generate throwaway gpg key: {gen.stderr}")

    contract_file = tmp_path / "c.yaml"
    contract_file.write_text(yaml.safe_dump(contract))
    sig = str(contract_file) + ".asc"
    sign = subprocess.run(
        ["gpg", "--batch", "--yes", "--armor", "--detach-sign", "-o", sig, str(contract_file)],
        env=env, capture_output=True, text=True,
    )
    assert sign.returncode == 0, sign.stderr

    # verify_gpg respects GNUPGHOME via the environment.
    ok_sig, message = gpgverify.verify_gpg(str(contract_file), sig, env=env)
    assert ok_sig, message

    # Tampering breaks verification.
    contract_file.write_text(yaml.safe_dump(contract) + "\n# tampered\n")
    ok_sig2, _ = gpgverify.verify_gpg(str(contract_file), sig, env=env)
    assert ok_sig2 is False
