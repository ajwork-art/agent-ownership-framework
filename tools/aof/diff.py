"""
Semantic diff for AOF contracts (``aof diff <old> <new>``).

Changes are classified as **material** or **cosmetic**. Material changes are any
change under the sections that govern what an agent may do or who is accountable:

- ``authority``                — autonomous decisions, prohibited actions, triggers, override
- ``data``                     — permitted/prohibited sources, sensitive-data handling
- ``ownership.escalation_path`` — escalation contacts and ordering
- ``signoff``                  — recorded owner sign-offs

Everything else is cosmetic. These are the contract's real section names.

Author: Anitha Jagadeesh — Enterprise Data AI Realities
License: MIT
"""

from typing import Any, Dict, List

MATERIAL_PREFIXES = ("authority", "data", "ownership.escalation_path", "signoff")


def _is_material(path: str) -> bool:
    for prefix in MATERIAL_PREFIXES:
        if path == prefix or path.startswith(prefix + ".") or path.startswith(prefix + "["):
            return True
    return False


def _walk(old: Any, new: Any, path: str, changes: List[Dict[str, Any]]) -> None:
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(set(old) | set(new)):
            child = f"{path}.{key}" if path else str(key)
            if key not in old:
                changes.append({"path": child, "change": "added", "old": None, "new": new[key]})
            elif key not in new:
                changes.append({"path": child, "change": "removed", "old": old[key], "new": None})
            else:
                _walk(old[key], new[key], child, changes)
    elif isinstance(old, list) and isinstance(new, list):
        for i in range(max(len(old), len(new))):
            child = f"{path}[{i}]"
            if i >= len(old):
                changes.append({"path": child, "change": "added", "old": None, "new": new[i]})
            elif i >= len(new):
                changes.append({"path": child, "change": "removed", "old": old[i], "new": None})
            else:
                _walk(old[i], new[i], child, changes)
    else:
        if old != new:
            changes.append({"path": path, "change": "changed", "old": old, "new": new})


def diff_contracts(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Return a classified diff between two parsed contracts.

    Result keys: ``material`` and ``cosmetic`` (lists of change records), and
    ``signoff_changed`` (whether anything under ``signoff`` changed).
    """
    changes: List[Dict[str, Any]] = []
    _walk(old, new, "", changes)

    material = [c for c in changes if _is_material(c["path"])]
    cosmetic = [c for c in changes if not _is_material(c["path"])]
    signoff_changed = any(
        c["path"] == "signoff" or c["path"].startswith("signoff.") or c["path"].startswith("signoff[")
        for c in changes
    )

    return {
        "material": material,
        "cosmetic": cosmetic,
        "signoff_changed": signoff_changed,
    }
