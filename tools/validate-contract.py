#!/usr/bin/env python3
"""
DEPRECATED — Agent Ownership Framework (AOF) standalone validator.

This standalone script is preserved for backward compatibility. It now delegates
to the installable ``aof`` package (``aof.validator``).

Please migrate to the packaged CLI:

    pip install aof-validate      # installs the `aof` command
    aof validate <path>           # file, directory, or glob

The legacy interface below (positional files, --verbose, --output json) still
works unchanged.

Author: Anitha Jagadeesh — Enterprise Data AI Realities
License: MIT
"""

import os
import sys

# Allow running directly from a checkout without installing the package.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aof.validator import run_standalone  # noqa: E402


def main() -> int:
    print(
        "\033[93m!\033[0m validate-contract.py is deprecated. "
        "Install the package and use `aof validate <path>` "
        "(pip install aof-validate).",
        file=sys.stderr,
    )
    return run_standalone(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
