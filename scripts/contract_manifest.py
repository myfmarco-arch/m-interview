#!/usr/bin/env python3
"""生成和校验 M-interview 的合同清单。"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "contracts/manifest.json"
FILES = [
    "contracts/artifacts.md",
    "contracts/module-contract.md",
    "contracts/validation-contract.md",
    "contracts/overlay-contract.md",
    "references/services/validation/core.md",
    "references/services/validation/expert.md",
    "references/services/validation/user-depth.md",
    "references/services/validation/focus-group.md",
    "references/services/validation/desk-research.md",
    "evals/conformance/cases.yaml",
    "evals/scoring.md",
]


def digest(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def build(revision: str | None = None) -> dict:
    old = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    files = {rel: digest(rel) for rel in FILES}
    if revision is None:
        revision = old.get("revision") or f"{dt.date.today().isoformat()}.1"
        if files != old.get("files"):
            date, _, number = revision.rpartition(".")
            revision = f"{dt.date.today().isoformat()}.{int(number) + 1 if date == dt.date.today().isoformat() and number.isdigit() else 1}"
    return {
        "contract": "m-interview-contract-v1",
        "revision": revision,
        "declaring_compatibility": None,
        "note": "合同、官方验证规则或 conformance 用例变化后运行 python scripts/contract_manifest.py write。",
        "files": files,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("write", "check"))
    parser.add_argument("--revision")
    args = parser.parse_args(argv)
    if args.command == "write":
        MANIFEST.write_text(json.dumps(build(args.revision), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"已写入 {MANIFEST.relative_to(ROOT)}")
        return 0
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors = []
    for rel in FILES:
        if rel not in data.get("files", {}):
            errors.append(f"manifest 未登记 {rel}")
        elif data["files"][rel] != digest(rel):
            errors.append(f"manifest hash mismatch: {rel}")
    if set(data.get("files", {})) != set(FILES):
        errors.append("manifest 包含未登记在合同清单中的文件")
    if errors:
        print("\n".join(f"error: {item}" for item in errors))
        return 1
    print(f"合同清单一致：{data.get('contract')}@{data.get('revision')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
