#!/usr/bin/env python3
"""M-interview 行为评测执行器。

流程：
  prepare 生成提示、夹具和人工评审模板。
  generate 用 --cmd 调用被测模型，保存 response.md。
  judge 用 --cmd 调用评审模型，保存 judgement.json；也可以人工填写。
  report 按评分规则计算结果。
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import math
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITES = {
    "conformance": "evals/conformance/cases.yaml",
    "modules": "evals/modules/cases.yaml",
    "product": "evals/products/interview-zh-default.yaml",
    "product-en": "evals/products/interview-en-minimal.yaml",
}
IGNORE = shutil.ignore_patterns(".git", "evals", "tests", "__pycache__", "*.pyc", ".DS_Store")


def load_yaml(path: Path):
    try:
        import yaml  # type: ignore
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except ImportError:
        result = subprocess.run(
            ["ruby", "-rjson", "-ryaml", "-e", "puts JSON.generate(YAML.load_file(ARGV[0]))", str(path)],
            capture_output=True, text=True, check=False,
        )
        if result.returncode:
            raise SystemExit(f"无法读取 YAML：{path}\n{result.stderr}")
        return json.loads(result.stdout)


def clean(text: str) -> str:
    return re.sub(r"(?<=[\u3000-\u9fff])\s+(?=[\u3000-\u9fff])", "", (text or "").strip())


def load_suite(name: str):
    if name in SUITES:
        data = load_yaml(ROOT / SUITES[name])
        return name, data.get("cases", []), []
    if name.startswith("overlay:"):
        overlay = ROOT / name.split(":", 1)[1]
        data = load_yaml(overlay)
        cases = []
        for rel in data.get("evals", []) or []:
            cases.extend((load_yaml(overlay.parent / rel) or {}).get("cases", []))
        return f"overlay-{data['id']}", cases, [str(overlay.relative_to(ROOT))]
    raise SystemExit(f"未知评测组：{name}")


def suites(names: list[str]) -> list[str]:
    return list(SUITES) if names == ["all"] else names


def fixture_block(case: dict, include_notes: bool = False) -> str:
    blocks = []
    for rel in case.get("fixtures", []) or []:
        text = (ROOT / rel).read_text(encoding="utf-8")
        if not include_notes:
            text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        blocks.append(f"附件 {Path(rel).name}：\n\n```\n{text.strip()}\n```")
    return "\n\n".join(blocks)


def prompt_for(case: dict) -> str:
    prompt = clean(case["request"])
    fixtures = fixture_block(case)
    return prompt + ("\n\n" + fixtures if fixtures else "") + "\n"


def iter_runs(out: Path):
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    for label, suite in manifest["suites"].items():
        for case_id in suite["cases"]:
            case_dir = out / label / case_id
            case = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
            for run_dir in sorted(case_dir.glob("run-*")):
                yield label, case, run_dir


def cmd_prepare(args) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "created": dt.datetime.now().isoformat(timespec="seconds"),
        "runs": args.runs,
        "skill_version": load_yaml(ROOT / "product.yaml").get("version"),
        "suites": {},
    }
    for suite_name in suites(args.suite):
        label, cases, overlays = load_suite(suite_name)
        manifest["suites"][label] = {"source": suite_name, "cases": []}
        for case in cases:
            if args.case and case["id"] not in args.case:
                continue
            case_dir = out / label / case["id"]
            case_dir.mkdir(parents=True, exist_ok=True)
            enriched = {**case, "overlays": overlays}
            (case_dir / "case.json").write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
            for number in range(1, args.runs + 1):
                run_dir = case_dir / f"run-{number}"
                run_dir.mkdir(parents=True, exist_ok=True)
                (run_dir / "prompt.md").write_text(prompt_for(case), encoding="utf-8")
                setup = ["# 评测准备", "", "使用全新会话，不保留上一用例的上下文。", ""]
                setup_data = case.get("setup", {}) or {}
                if overlays:
                    setup += ["启用 overlay：", "", *[f"- {item}" for item in overlays], ""]
                if setup_data.get("product"):
                    setup += [f"产品：{setup_data['product']}", ""]
                setup += ["把 prompt.md 的全部内容作为一条消息发送，完整回答保存为 response.md。"]
                (run_dir / "setup.md").write_text("\n".join(setup) + "\n", encoding="utf-8")
                template = {
                    "expected": [{"index": i, "met": None, "evidence": ""} for i in range(1, len(case.get("expected", [])) + 1)],
                    "forbidden": [{"index": i, "occurred": None, "evidence": ""} for i in range(1, len(case.get("forbidden", [])) + 1)],
                    "notes": "",
                    "judge": "human",
                }
                (run_dir / "judgement.template.json").write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
            manifest["suites"][label]["cases"].append(case["id"])
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已准备 {sum(len(item['cases']) for item in manifest['suites'].values())} 个用例 × {args.runs} 次运行：{out}")
    return 0


def run_command(command: str, prompt: str, cwd: Path, timeout: int):
    return subprocess.run(shlex.split(command), input=prompt, capture_output=True, text=True, cwd=cwd, timeout=timeout)


def generate_one(item, args):
    label, case, run_dir = item
    target = run_dir / "response.md"
    if target.exists() and not args.overwrite:
        return True, label, case["id"], run_dir.name
    workspace = run_dir / "workspace"
    if workspace.exists():
        shutil.rmtree(workspace)
    skill_dir = workspace / args.install_path
    skill_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT, skill_dir, ignore=IGNORE)
    setup = case.get("setup", {}) or {}
    if setup.get("product"):
        (skill_dir / "local.yaml").write_text(
            f"schema_version: 1\nproduct: {setup['product']}\n", encoding="utf-8"
        )
    try:
        prompt = (
            f"请使用当前工作区中的 M-interview Skill：{args.install_path}/SKILL.md。"
            "先读取该 Skill 的入口和按需引用，再严格遵守其规则完成下面的用户请求。\n\n"
            + (run_dir / "prompt.md").read_text(encoding="utf-8")
        )
        result = run_command(args.cmd, prompt, workspace, args.timeout)
    except subprocess.TimeoutExpired:
        result = None
    if result is None or result.returncode != 0 or not result.stdout.strip():
        message = "timeout" if result is None else f"exit={result.returncode}\n{result.stderr}"
        (run_dir / "generate.error.txt").write_text(message, encoding="utf-8")
        return False, label, case["id"], run_dir.name
    target.write_text(result.stdout, encoding="utf-8")
    (run_dir / "generate.error.txt").unlink(missing_ok=True)
    if not args.keep_workspace:
        shutil.rmtree(workspace)
    return True, label, case["id"], run_dir.name


def cmd_generate(args) -> int:
    items = [
        item for item in iter_runs(Path(args.out))
        if args.overwrite or not (item[2] / "response.md").exists()
    ]
    failures = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(generate_one, item, args) for item in items]
        for future in concurrent.futures.as_completed(futures):
            ok, label, case_id, run_name = future.result()
            print(f"[{'完成' if ok else '失败'}] {label}/{case_id}/{run_name}")
            failures += not ok
    return 1 if failures else 0


def numbered(items):
    return "\n".join(f"{i}. {clean(item)}" for i, item in enumerate(items, 1)) or "（无）"


def judge_prompt(case: dict, response: str) -> str:
    template = (ROOT / "evals/judge-prompt.md").read_text(encoding="utf-8")
    fixtures = fixture_block(case, include_notes=True)
    return template.format(
        case_id=case["id"], request=clean(case["request"]),
        fixtures=("\n用户提供的附件：\n\n" + fixtures) if fixtures else "",
        expected=numbered(case.get("expected", [])),
        forbidden=numbered(case.get("forbidden", [])), response=response.strip(),
    )


def extract_json(text: str):
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    raw = match.group(1) if match else text[text.find("{"): text.rfind("}") + 1]
    return json.loads(raw)


def judge_one(item, args):
    label, case, run_dir = item
    response = run_dir / "response.md"
    target = run_dir / "judgement.json"
    if not response.exists() or (target.exists() and not args.overwrite):
        return True, label, case["id"], run_dir.name
    try:
        prompt = judge_prompt(case, response.read_text(encoding="utf-8"))
        (run_dir / "judge-prompt.txt").write_text(prompt, encoding="utf-8")
        result = run_command(args.cmd, prompt, run_dir, args.timeout)
        data = extract_json(result.stdout)
        data["judge"] = args.cmd
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        (run_dir / "judge.error.txt").unlink(missing_ok=True)
        return True, label, case["id"], run_dir.name
    except Exception as exc:  # noqa: BLE001
        (run_dir / "judge.error.txt").write_text(str(exc), encoding="utf-8")
        return False, label, case["id"], run_dir.name


def cmd_judge(args) -> int:
    items = [
        item for item in iter_runs(Path(args.out))
        if (item[2] / "response.md").exists()
        and (args.overwrite or not (item[2] / "judgement.json").exists())
    ]
    failures = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(judge_one, item, args) for item in items]
        for future in concurrent.futures.as_completed(futures):
            ok, label, case_id, run_name = future.result()
            print(f"[{'完成' if ok else '失败'}] {label}/{case_id}/{run_name}")
            failures += not ok
    return 1 if failures else 0


def verdict(case: dict, judgement: dict):
    expected = {item["index"]: item for item in judgement.get("expected", [])}
    forbidden = {item["index"]: item for item in judgement.get("forbidden", [])}
    expected_ids = set(range(1, len(case.get("expected", [])) + 1))
    forbidden_ids = set(range(1, len(case.get("forbidden", [])) + 1))
    if set(expected) != expected_ids or set(forbidden) != forbidden_ids:
        return "invalid", "评审条目数量不匹配"
    if any(not isinstance(item.get("met"), bool) for item in expected.values()):
        return "invalid", "expected.met 必须是布尔值"
    if any(not isinstance(item.get("occurred"), bool) for item in forbidden.values()):
        return "invalid", "forbidden.occurred 必须是布尔值"
    if any(item["occurred"] for item in forbidden.values()):
        return "fail", "出现禁止行为"
    unmet = [index for index, item in expected.items() if not item["met"]]
    if not unmet:
        return "pass", ""
    return ("partial", "未满足 1 项预期") if len(unmet) == 1 else ("fail", f"未满足预期：{unmet}")


def cmd_report(args) -> int:
    out = Path(args.out)
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    results = {"created": dt.datetime.now().isoformat(timespec="seconds"), "skill_version": manifest.get("skill_version"), "suites": {}}
    lines = ["# 评测报告", "", f"- Skill 版本：{manifest.get('skill_version')}", f"- 被测模型：{args.model or '未填写'}", f"- 评审方式：{args.judge_label or '未填写'}", f"- 每个用例运行次数：{manifest['runs']}", ""]
    overall = True
    for label, suite in manifest["suites"].items():
        rows = []
        for case_id in suite["cases"]:
            case_dir = out / label / case_id
            case = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
            run_results = []
            for run_dir in sorted(case_dir.glob("run-*")):
                judgement = run_dir / "judgement.json"
                run_results.append(("missing", "缺少 judgement.json") if not judgement.exists() else verdict(case, json.loads(judgement.read_text(encoding="utf-8"))))
            passed = sum(status == "pass" for status, _ in run_results)
            needed = len(run_results) if case.get("blocking", True) else (math.ceil(2 * len(run_results) / 3) if run_results else 1)
            status = "pass" if run_results and all(v not in {"missing", "invalid"} for v, _ in run_results) and passed >= needed and not any(v == "fail" and reason == "出现禁止行为" for v, reason in run_results) else "fail"
            rows.append({"id": case_id, "blocking": case.get("blocking", True), "status": status, "pass_runs": passed, "runs": len(run_results), "details": run_results})
        blocking_ok = all(row["status"] == "pass" for row in rows if row["blocking"] or label == "conformance")
        non_blocking = [row for row in rows if not row["blocking"]]
        allowed = max(1, len(non_blocking) // 5) if non_blocking else 0
        non_blocking_ok = sum(row["status"] != "pass" for row in non_blocking) <= allowed
        suite_ok = blocking_ok and non_blocking_ok
        overall = overall and suite_ok
        results["suites"][label] = {"passed": suite_ok, "cases": rows}
        lines += [f"## {label}：{'通过' if suite_ok else '未通过'}", "", "| 用例 | 阻断 | 结果 | 通过次数 |", "|---|---|---|---|"]
        lines += [f"| {row['id']} | {'是' if row['blocking'] else '否'} | {row['status']} | {row['pass_runs']}/{row['runs']} |" for row in rows]
        lines.append("")
    (out / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0 if overall else 1


def cmd_list(args) -> int:
    for name in suites(args.suite):
        label, cases, _ = load_suite(name)
        print(f"## {label}（{len(cases)} 个用例）")
        for case in cases:
            print(f"- {case['id']} kind={case.get('kind')} blocking={case.get('blocking', True)}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    item = sub.add_parser("list"); item.add_argument("--suite", nargs="+", default=["all"]); item.set_defaults(func=cmd_list)
    item = sub.add_parser("prepare"); item.add_argument("--suite", nargs="+", default=["conformance"]); item.add_argument("--case", nargs="*"); item.add_argument("--runs", type=int, default=3); item.add_argument("--out", default=f"evals/runs/{dt.date.today().isoformat()}"); item.set_defaults(func=cmd_prepare)
    item = sub.add_parser("generate"); item.add_argument("--out", required=True); item.add_argument("--cmd", required=True); item.add_argument("--install-path", default=".codex/skills/m-interview"); item.add_argument("--timeout", type=int, default=900); item.add_argument("--workers", type=int, default=1); item.add_argument("--overwrite", action="store_true"); item.add_argument("--keep-workspace", action="store_true"); item.set_defaults(func=cmd_generate)
    item = sub.add_parser("judge"); item.add_argument("--out", required=True); item.add_argument("--cmd", required=True); item.add_argument("--timeout", type=int, default=300); item.add_argument("--workers", type=int, default=1); item.add_argument("--overwrite", action="store_true"); item.set_defaults(func=cmd_judge)
    item = sub.add_parser("report"); item.add_argument("--out", required=True); item.add_argument("--model"); item.add_argument("--judge-label"); item.set_defaults(func=cmd_report)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
