"""Extract all `@frappe.whitelist()` decorated functions from lifegence_agent.

Usage:
    python3 apps/lifegence_agent/lifegence_agent/scripts/extract_whitelist_apis.py

Writes the list to `apps/lifegence_agent/e2e/fixtures/all-whitelist-apis.json`.
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys


def _has_whitelist(node: ast.FunctionDef) -> bool:
    for dec in node.decorator_list:
        if isinstance(dec, ast.Call):
            func = dec.func
        else:
            func = dec
        name = ""
        if isinstance(func, ast.Attribute):
            name = func.attr
        elif isinstance(func, ast.Name):
            name = func.id
        if name == "whitelist":
            return True
    return False


def extract(app_root: pathlib.Path) -> list[str]:
    app_parent = app_root.parent
    found: list[str] = []
    for py in app_root.rglob("*.py"):
        if "tests/" in str(py) or "__pycache__" in str(py):
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and _has_whitelist(node):
                rel = py.relative_to(app_parent).with_suffix("")
                dotted = ".".join(rel.parts)
                found.append(f"{dotted}.{node.name}")
    return sorted(set(found))


def main() -> int:
    app_root = pathlib.Path(__file__).resolve().parents[1]  # lifegence_agent/
    out = (
        app_root.parent
        / "e2e"
        / "fixtures"
        / "all-whitelist-apis.json"
    )
    methods = extract(app_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(methods, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ Extracted {len(methods)} whitelist methods → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
