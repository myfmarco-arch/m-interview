#!/usr/bin/env python3
"""Lightweight repository checks for M-interview."""

from __future__ import annotations

import json
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def yaml_load(path: Path):
    try:
        import yaml  # type: ignore
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except ImportError:
        ruby = subprocess.run(
            ["ruby", "-rjson", "-ryaml", "-e", "puts JSON.generate(YAML.load_file(ARGV[0]))", str(path)],
            capture_output=True, text=True, check=False,
        )
        if ruby.returncode:
            raise RuntimeError(ruby.stderr.strip() or f"cannot parse {path}")
        return json.loads(ruby.stdout)


def markdown_links(path: Path):
    text = path.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)", text):
        if target.startswith(("http://", "https://", "codex://")):
            continue
        yield path.parent / target


def rule_ids():
    found: dict[str, Path] = {}
    errors: list[str] = []
    severities: dict[str, str] = {}
    paths = list((ROOT / "references/services").glob("*.md"))
    paths.extend((ROOT / "references/services/validation").glob("*.md"))
    paths.extend((ROOT / "references/products").rglob("*.md"))
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for rule_id in re.findall(r"`([a-z][a-z0-9-]*\.[a-z][a-z0-9-]*)`", text):
            if rule_id in found and found[rule_id] != path:
                errors.append(f"duplicate rule id {rule_id}: {found[rule_id]} and {path}")
            found[rule_id] = path
        for rule_id, severity in re.findall(r"\|\s*`([^`]+)`\s*\|[^|]*\|\s*(error|warning|info)\s*\|", text):
            if rule_id in severities and severities[rule_id] != severity:
                errors.append(f"conflicting severity for {rule_id}: {severities[rule_id]} and {severity}")
            severities[rule_id] = severity
    return found, severities, errors


def nested_string_values(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from nested_string_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_string_values(child)
    elif isinstance(value, str):
        yield value


def main() -> int:
    errors: list[str] = []
    configs = [ROOT / "product.yaml", ROOT / "local.example.yaml"]
    configs.extend(sorted((ROOT / "references").rglob("*.yaml")))
    for config in configs:
        try:
            yaml_load(config)
        except Exception as exc:
            errors.append(f"yaml: {config}: {exc}")
    product = yaml_load(ROOT / "product.yaml")
    if isinstance(product, dict):
        for section in ("contracts", "services", "modules", "validation", "products", "adapters", "evals"):
            value = product.get(section, {})
            files = []
            if isinstance(value, dict):
                files.extend(v for k, v in value.items() if k != "default" and isinstance(v, str))
                for item in value.get("always", []) if section == "validation" else []:
                    if isinstance(item, str): files.append(item)
                for item in value.get("when", []) if section == "validation" else []:
                    if isinstance(item, dict) and isinstance(item.get("file"), str): files.append(item["file"])
                if section == "products":
                    for cfg in value.values():
                        if isinstance(cfg, dict): files.extend(v for v in cfg.values() if isinstance(v, str))
                if section == "adapters":
                    files.extend(v for v in value.get("available", {}).values() if isinstance(v, str))
                if section in {"modules", "products", "evals"}:
                    files.extend(nested_string_values(value))
            for rel in files:
                if not (ROOT / rel).exists(): errors.append(f"missing referenced file: {rel}")
    for overlay in (ROOT / "references/overlays").rglob("overlay.yaml"):
        try:
            data = yaml_load(overlay)
        except Exception as exc:
            errors.append(f"yaml: {overlay}: {exc}")
            continue
        if not isinstance(data, dict):
            continue
        allowed_overrides = {"workflow", "writing", "brief_format", "guide_format", "naming", "research_design", "methods", "knowledge", "adapters"}
        overrides = data.get("overrides", {})
        if isinstance(overrides, dict):
            for key in overrides:
                if key not in allowed_overrides:
                    errors.append(f"overlay uses non-overridable target: {overlay}: {key}")
        for item in overrides.values() if isinstance(overrides, dict) else []:
            if isinstance(item, dict) and isinstance(item.get("file"), str):
                if item.get("mode") not in {"replace", "extend", "add"}:
                    errors.append(f"overlay has invalid mode: {overlay}: {item.get('mode')}")
                if not (overlay.parent / item["file"]).exists():
                    errors.append(f"missing overlay file: {overlay.parent / item['file']}")
        if "contracts" in data or "validation" in data and not isinstance(data["validation"], dict):
            errors.append(f"overlay cannot replace contracts or malformed validation: {overlay}")
        validation = data.get("validation", {})
        for item in validation.get("add", []) if isinstance(validation, dict) else []:
            if isinstance(item, dict) and isinstance(item.get("file"), str):
                if not (overlay.parent / item["file"]).exists():
                    errors.append(f"missing overlay validation: {overlay.parent / item['file']}")
        ethics_defaults = data.get("ethics_defaults")
        if ethics_defaults is not None:
            if not isinstance(ethics_defaults, dict) or ethics_defaults.get("mode") != "add" or not isinstance(ethics_defaults.get("file"), str):
                errors.append(f"overlay ethics_defaults must use mode: add and a file: {overlay}")
            elif not (overlay.parent / ethics_defaults["file"]).exists():
                errors.append(f"missing overlay ethics defaults: {overlay.parent / ethics_defaults['file']}")
        for rel in data.get("evals", []) if isinstance(data.get("evals"), list) else []:
            if isinstance(rel, str) and not (overlay.parent / rel).exists():
                errors.append(f"missing overlay eval: {overlay.parent / rel}")
    rules, severities, rule_errors = rule_ids()
    errors.extend(rule_errors)
    for path in (ROOT / "references/modules").rglob("*.md"):
        for rule_id in re.findall(r"`([a-z][a-z0-9-]*\.[a-z][a-z0-9-]*)`", path.read_text(encoding="utf-8")):
            if rule_id not in rules:
                errors.append(f"unknown module rule reference {rule_id}: {path}")
    conformance_targets: set[str] = set()
    for path in (ROOT / "evals").rglob("*.yaml"):
        try:
            data = yaml_load(path)
        except Exception as exc:
            errors.append(f"yaml: {path}: {exc}")
            continue
        if not isinstance(data, dict): continue
        for case in data.get("cases", []) if isinstance(data.get("cases"), list) else []:
            for target in case.get("targets", []) if isinstance(case, dict) else []:
                if target and target not in rules and not target.startswith("format."):
                    errors.append(f"unknown eval target {target}: {path}")
                if target and "conformance" in str(path):
                    conformance_targets.add(target)
    for rule_id, severity in severities.items():
        if severity == "error" and rule_id not in conformance_targets and not rule_id.startswith("format."):
            errors.append(f"error rule has no conformance case: {rule_id}")
    manifest = ROOT / "contracts/manifest.json"
    try:
        manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
        for rel, expected in manifest_data.get("files", {}).items():
            target = ROOT / rel
            if not target.exists():
                errors.append(f"manifest file missing: {rel}")
                continue
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            if actual != expected:
                errors.append(f"manifest hash mismatch: {rel}")
    except Exception as exc:
        errors.append(f"manifest: {exc}")
    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    product_text = (ROOT / "product.yaml").read_text(encoding="utf-8")
    skill_version = re.search(r"^  version:\s*([^\s]+)", skill_text, flags=re.MULTILINE)
    product_version = re.search(r"^version:\s*([^\s]+)", product_text, flags=re.MULTILINE)
    if not skill_version or not product_version or skill_version.group(1) != product_version.group(1):
        errors.append("version mismatch between SKILL.md and product.yaml")
    if product_version and f"[{product_version.group(1)}]" not in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"):
        errors.append("product version missing from CHANGELOG.md")
    for path in ROOT.rglob("*.md"):
        if (ROOT / "evals/runs") in path.parents:
            continue
        if "/Users/" in path.read_text(encoding="utf-8"):
            errors.append(f"absolute local path in {path}")
        for target in markdown_links(path):
            if not target.exists(): errors.append(f"broken link in {path}: {target}")
    if errors:
        print("\n".join(f"error: {item}" for item in errors))
        return 1
    print("M-interview repository checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
