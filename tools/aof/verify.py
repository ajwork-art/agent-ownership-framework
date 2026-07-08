"""
Detached-signature verification for AOF contracts (``aof verify``).

This is an **optional** integrity check. AOF does not ship a PKI, does not store
or generate private keys, and does not require signing — signatures are a
defense-in-depth option for teams that want cryptographic proof that a contract
file was approved by a specific key holder.

GPG is implemented here (ubiquitous). A Sigstore/cosign recipe is documented in
docs/INTEGRATION.md. Signing itself is performed out of band, for example:

    gpg --armor --detach-sign my-agent.yaml        # produces my-agent.yaml.asc

Author: Anitha Jagadeesh — Enterprise Data AI Realities
License: MIT
"""

import os
import shutil
import subprocess
from typing import Optional, Tuple


def default_signature_path(contract_path: str) -> Optional[str]:
    """Return the conventional detached-signature path next to a contract, if any."""
    for ext in (".asc", ".sig", ".gpg"):
        candidate = contract_path + ext
        if os.path.exists(candidate):
            return candidate
    return None


def gpg_available() -> bool:
    return shutil.which("gpg") is not None


def verify_gpg(contract_path: str, signature_path: str) -> Tuple[bool, str]:
    """Verify a detached GPG signature over ``contract_path``.

    Returns (ok, message). Requires the signer's public key to already be in the
    local GnuPG keyring; key distribution and trust are the operator's
    responsibility.
    """
    if not gpg_available():
        return False, "gpg is not installed — install GnuPG to verify signatures."
    if not os.path.exists(contract_path):
        return False, f"Contract not found: {contract_path}"
    if not os.path.exists(signature_path):
        return False, f"Signature not found: {signature_path}"

    try:
        proc = subprocess.run(
            ["gpg", "--verify", signature_path, contract_path],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as e:  # pragma: no cover
        return False, f"gpg invocation failed: {e}"

    # gpg writes verification details to stderr for both success and failure.
    detail = (proc.stderr or proc.stdout or "").strip()
    if proc.returncode == 0:
        return True, detail or "Good signature."
    return False, detail or "Signature verification failed."
