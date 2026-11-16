#!/usr/bin/env python3
"""Dependency-free heuristic checks for an interview brief and field guide.

The checks are heuristics. Warnings point to lines worth a human look; they do not
replace the model's rule-by-rule self-check or a researcher's review.
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "references/products/interview-zh-default/profile.yaml"

FORBIDDEN_GUIDE_SECTIONS = {
    "本模块目标", "模块目标", "对应研究问题", "导入话术", "主持人注意",
    "主持人注意事项", "重点观察", "模块小结", "研究目标", "研究信息",
    "方法选择", "整体访谈思路", "访前准备", "时间与模块预算", "评估说明",
    "Research goal", "Research information", "Method", "Interview flow",
    "Preparation", "Moderator notes", "Moderator notes and timing",
}
PLACEHOLDERS = ("待定", "待确认", "TODO", "TBD", "要拿到", "待回头")
PROCESS_MARKERS = (
    "当前工作区", "下面是整理", "我将", "生成过程", "模型", "方法说明",
    "current workspace", "here is the", "I will", "generation process", "method explanation",
)
DRAFT_SLOT = re.compile(r"【执行前补[：:][^】]*】|\[Confirm before fieldwork:[^\]]*\]")

# Wording heuristics. Keep lists short and specific to limit false alarms.
# 团队大纲里常用“如何”“是否”“体验如何”“维度”“因素”，这些不算 AI 腔，不在清单里。
AI_PHRASES = (
    "分享一下", "分享您", "和我们分享", "有何看法", "整体而言", "总体而言", "具体而言",
    "是什么促使", "能否请您", "请您描述", "请阐述", "深入探讨", "洞察", "赋能", "价值点",
    "对于您来说", "非常感谢您的分享",
    "could you share", "can you share", "overall experience", "in terms of", "how do you feel about",
)
# 为了显得口语而硬加的词，读起来反而不像团队写法。
FORCED_COLLOQUIAL = ("啥", "咋", "拍板", "弄过来", "弄回来", "怎么弄", "弄的")
JARGON = ("痛点", "核心诉求", "用户价值", "心智", "底层逻辑", "抓手", "闭环", "触点", "JTBD", "pain point")
HYPOTHETICAL = re.compile(
    r"会不会|愿不愿意|愿意.{0,8}(?:吗|？|\?)|打算|将来|以后会|下次会|假如|假设|如果.{0,25}(?:会|还会)"
    r"|would you|will you|if there were"
)
LEADING = re.compile(
    r"最吸引|最喜欢|最满意|好用的地方|方便的地方|是不是.{0,12}(?:很|更|特别|比较)|难道|不觉得|不是.{0,8}吗"
    r"|很多麻烦|多大帮助|解决了.{0,8}(?:问题|麻烦)|don't you think|how much did .* help"
)
UNEXPERIENCED = re.compile(r"没用过.{0,12}(?:也|请).{0,12}(?:好不好|评价|怎么样|满意)|never used.{0,30}(?:rate|how good)", re.IGNORECASE)
CLAUSE_QUESTION = re.compile(r"怎么|为什么|什么|哪|吗|多少")
STIMULUS_SECTION = re.compile(r"概念|原型|刺激物|看图|图片|演示|concept|prototype|stimul", re.IGNORECASE)
OPEN_WORDS = re.compile(r"怎么|什么|哪|讲|说说|聊聊|多少|为什么|几|how|what|which|when|where|why|tell", re.IGNORECASE)
CLOSED_END = re.compile(r"(?:吗|是不是[^？?]*|是否[^？?]*)[？?]\s*$")

MAIN_RE = re.compile(r"^\s*(\d+)\.\s+\*\*(.+?)\*\*\s*$")
# 团队格式：#### 【标签】问句？ 作为主问题；不带问号、不带【】的小标题只是分组。
HEADING_RE = re.compile(r"^#{3,6}\s+(.+?)\s*$")
PROBE_RE = re.compile(r"^(\s*)[-*]\s+(.+?)\s*$")
# 提示清单是一行类别枚举，按行扫读，不按口语长度要求。
CHECKLIST_RE = re.compile(r"^(?:没提到的逐项问|逐项问|prompt-list|Prompt list)")
RANGE_RE = re.compile(r"第\s*(\d+)\s*[–—-]\s*(\d+)\s*分钟|minutes?\s*(\d+)\s*[–—-]\s*(\d+)", re.IGNORECASE)
# 团队格式：## 二、换机过程（13mins） / (5min) / （10分钟） / （30-40 min）。区间取下限。
DURATION_RE = re.compile(r"[（(]\s*(\d+)\s*(?:[-–—~]\s*(\d+))?\s*(?:mins?|分钟)\s*[）)]", re.IGNORECASE)
BRANCH_TAG = re.compile(r"^\[[^\]\n]{1,30}\][：:]\s*|^(?:若|如果|If)[^：:]{0,30}[：:]\s*")
OPENING_WORDS = ("开场", "热身", "Opening")
CLOSING_WORDS = ("收尾", "总结", "补充问题", "Closing")


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def load_profile(path: Path) -> dict:
    """Read the few numeric defaults lint needs without a YAML dependency."""
    profile = {
        "guide_line_warning": 95,
        "max_main_questions_per_module": 3,
        "max_probes_per_main_question": 8,
        "probe_minutes_per_line": 1.5,
        "max_main_question_chars": 70,
        "max_probe_chars": 40,
        "minutes": {"user-depth": (7, 15), "expert": (7, 15), "focus-group": (10, 20)},
    }
    if not path.exists():
        return profile
    text = path.read_text(encoding="utf-8")
    for key in ("guide_line_warning", "max_main_questions_per_module", "max_probes_per_main_question",
                "probe_minutes_per_line", "max_main_question_chars", "max_probe_chars"):
        match = re.search(rf"^\s+{key}:\s*(\d+(?:\.\d+)?)\s*$", text, flags=re.MULTILINE)
        if match:
            value = float(match.group(1))
            profile[key] = int(value) if value.is_integer() else value
    block = re.search(r"^\s+minutes_per_main_question:\s*\n((?:\s{4,}[a-z-]+:\s*\d+-\d+\s*\n)+)", text, flags=re.MULTILINE)
    if block:
        for name, low, high in re.findall(r"([a-z-]+):\s*(\d+)-(\d+)", block.group(1)):
            profile["minutes"][name] = (int(low), int(high))
    return profile


def plain(text: str) -> str:
    text = re.sub(r"\*\*|`", "", text).strip()
    text = re.sub(r"^【[^】]{1,12}】\s*", "", text)
    return BRANCH_TAG.sub("", text)


def char_count(text: str) -> int:
    return len(re.sub(r"\s", "", plain(text)))


def check_brief(text: str, errors: list, warnings: list) -> None:
    english = "Research questions" in text or "Research nature" in text
    required = (
        (("SRQ", "Research questions"), ("Research nature",), ("Method",), ("Consent", "Recording"), ("Time", "Duration"))
        if english
        else (("SRQ", "子研究问题", "研究问题"), ("研究性质",), ("方法",), ("同意", "记录", "隐私"), ("时间", "时长"))
    )
    for alternatives in required:
        if not any(item in text for item in alternatives):
            errors.append(("format.brief-required", f"brief: missing one of {' / '.join(alternatives)}"))
    table_headers = [line for line in text.splitlines() if line.strip().startswith("|") and "SRQ" in line]
    if "SRQ" in text and not table_headers:
        warnings.append(("design.srq-coverage", "brief: no table maps modules or methods to SRQ"))
    if not any(word in text for word in ("样本", "场次", "Sample", "sessions")):
        warnings.append(("design.sample", "brief: no sample line (sessions, segments, who is not in the sample)"))


def detect_format(header: str) -> str:
    if re.search(r"座谈会|焦点小组|focus group", header, flags=re.IGNORECASE):
        return "focus-group"
    if re.search(r"专家|expert", header, flags=re.IGNORECASE):
        return "expert"
    return "user-depth"


def find_duration(text: str, header: str) -> int | None:
    match = re.search(r"(?:预计?时长|Duration)\s*[：:|｜]?\s*(\d+)\s*(?:分钟|minutes?)", text, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r"(?<![第\d–—-])\s*(\d+)\s*(?:分钟|-?minutes?|mins?\b)", header, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def split_sections(lines: list[str]) -> list[dict]:
    sections = []
    current = {"title": "", "lines": [], "kind": "header"}
    for number, line in enumerate(lines, start=1):
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            sections.append(current)
            title = heading.group(1)
            kind = "opening" if any(w in title for w in OPENING_WORDS) else "closing" if any(w in title for w in CLOSING_WORDS) else "core"
            current = {"title": title, "lines": [], "kind": kind}
            continue
        current["lines"].append((number, line))
    sections.append(current)
    return sections


def check_wording(number: int, raw: str, role: str, profile: dict, warnings: list) -> None:
    text = plain(raw)
    snippet = f"line {number}: {text[:60]}"
    marks = text.count("？") + text.count("?")
    if (role == "main" and marks > 1) or marks > 2:
        warnings.append(("question.single-task", f"guide {snippet} (more than {'one question' if role == 'main' else 'two questions'})"))
    for phrase in AI_PHRASES:
        if phrase.lower() in text.lower():
            warnings.append(("format.natural-wording", f"guide {snippet} (written or chatbot phrasing: '{phrase}')"))
            break
    for phrase in FORCED_COLLOQUIAL:
        if phrase in text:
            warnings.append(("format.natural-wording", f"guide {snippet} (forced colloquial word: '{phrase}')"))
            break
    for word in JARGON:
        if word.lower() in text.lower():
            warnings.append(("question.knowledge-boundary", f"guide {snippet} (researcher term: '{word}')"))
            break
    if UNEXPERIENCED.search(text):
        warnings.append(("question.experience-required", f"guide {snippet} (asks people without the experience to evaluate it)"))
    if LEADING.search(text):
        warnings.append(("question.no-leading", f"guide {snippet} (presupposes an answer)"))
    if role == "main":
        clauses = [c for c in re.split(r"[，,；;]", text) if CLAUSE_QUESTION.search(c)]
        if len(clauses) >= 3:
            warnings.append(("question.single-task", f"guide {snippet} (several questions joined by commas)"))
        if HYPOTHETICAL.search(text):
            warnings.append(("question.no-hypothetical", f"guide {snippet} (future intention or hypothetical as main question)"))
        if CLOSED_END.search(text) and not OPEN_WORDS.search(text):
            warnings.append(("question.open-form", f"guide {snippet} (yes/no main question)"))
        if char_count(raw) > profile["max_main_question_chars"]:
            warnings.append(("format.natural-wording", f"guide {snippet} (main question longer than {profile['max_main_question_chars']} characters)"))
    elif role == "probe" and not CHECKLIST_RE.match(text) and char_count(raw) > profile["max_probe_chars"]:
        warnings.append(("format.natural-wording", f"guide {snippet} (probe longer than {profile['max_probe_chars']} characters)"))


def check_guide(text: str, errors: list, warnings: list, profile: dict, allow_template: bool = False, draft: bool = False) -> None:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    lines = text.splitlines()
    if len(lines) > 120:
        warnings.append(("format.guide-length", "guide: over 120 lines; this will not fit on two pages"))
    if len(lines) > profile["guide_line_warning"]:
        warnings.append(("format.guide-length", "guide: over the concise content budget; remove nonessential text before layout compression"))
    if not any(word in text for word in CLOSING_WORDS):
        errors.append(("format.guide-closing", "guide: missing a closing module (收尾 / 总结)"))
    for marker in PLACEHOLDERS:
        if marker in text:
            errors.append(("guide.no-placeholder", f"guide: unresolved internal marker '{marker}'"))
    if not allow_template:
        bracket_tokens = [token for token in re.findall(r"\[[^\]\n]{1,40}\](?![(：:])", text) if not DRAFT_SLOT.fullmatch(token)]
        if bracket_tokens:
            errors.append(("guide.no-placeholder", f"guide: unresolved placeholders: {', '.join(bracket_tokens[:4])}"))
    for marker in PROCESS_MARKERS:
        if marker in text:
            errors.append(("format.guide-minimal", f"guide: process text '{marker}' does not belong in the field guide"))

    sections = split_sections(lines)
    header = "\n".join(line for _, line in sections[0]["lines"])
    headings = {m.group(1).strip() for m in re.finditer(r"^#{1,6}\s+(.+?)\s*$", text, flags=re.MULTILINE)}
    for heading in sorted(headings & FORBIDDEN_GUIDE_SECTIONS):
        errors.append(("format.guide-hand-card", f"guide: '{heading}' belongs in the brief"))

    slots = [(section["kind"], number) for section in sections for number, line in section["lines"] if DRAFT_SLOT.search(line)]
    if slots and not draft:
        errors.append(("guide.no-placeholder", "guide: draft slots ('【执行前补：…】' / '[Confirm before fieldwork: …]') are allowed only in a draft (use --draft); a ready guide must have none"))
    for kind, number in slots:
        if draft and kind != "opening":
            errors.append(("guide.no-placeholder", f"guide line {number}: draft slots are allowed only in the opening"))

    duration = find_duration(text, header)
    interview_format = detect_format(header)
    ranges = []
    durations = []
    for section in sections[1:]:
        match = RANGE_RE.search(section["title"])
        if match:
            start, end = [int(x) for x in match.groups() if x is not None]
            section["minutes"] = end - start
            ranges.append((start, end))
            continue
        match = DURATION_RE.search(section["title"])
        if match:
            section["minutes"] = int(match.group(1))
            durations.append(int(match.group(1)))
    if durations and not ranges:
        if duration and sum(durations) > duration:
            errors.append(("design.time-budget", f"guide: module time ({sum(durations)} min) exceeds interview duration ({duration} min)"))
        elif not duration and not allow_template:
            warnings.append(("design.time-budget", "guide: total duration not found in the header; time total was not checked"))
    elif ranges:
        if any(end <= start for start, end in ranges):
            errors.append(("design.time-budget", "guide: invalid time range"))
        if duration:
            total = sum(end - start for start, end in ranges)
            if max(end for _, end in ranges) > duration or total > duration:
                errors.append(("design.time-budget", f"guide: module time ({total} min, ends at {max(end for _, end in ranges)}) exceeds interview duration ({duration} min)"))
        elif not allow_template:
            warnings.append(("design.time-budget", "guide: total duration not found in the header; time total was not checked"))
    elif not allow_template and "##" in text and any(word in text for word in CLOSING_WORDS):
        warnings.append(("format.time-range", "guide: no module durations found, e.g. '## 二、换机过程（15mins）'"))

    core_sections = [section for section in sections[1:] if section["kind"] == "core"]
    if len(core_sections) > 1 and STIMULUS_SECTION.search(core_sections[0]["title"]):
        warnings.append(("question.order", f"guide: stimulus module '{core_sections[0]['title']}' comes before participants describe their own experience"))

    numbers: list[int] = []
    core_questions = 0
    core_minutes = 0
    for section in sections[1:]:
        mains = 0
        probes_for_current = 0
        base_indent = None
        for number, line in section["lines"]:
            main = MAIN_RE.match(line)
            heading = HEADING_RE.match(line)
            probe = PROBE_RE.match(line)
            main_text = None
            if main:
                main_text = main.group(2)
                numbers.append(int(main.group(1)))
            elif heading:
                title = re.sub(r"\*\*", "", heading.group(1)).strip()
                if title.startswith("【") or "？" in title or "?" in title:
                    main_text = title
                else:
                    continue
            if main_text is not None:
                if probes_for_current > profile["max_probes_per_main_question"]:
                    warnings.append(("format.question-count", f"guide: question before line {number} has {probes_for_current} first-level probes; maximum is {profile['max_probes_per_main_question']}"))
                probes_for_current = 0
                base_indent = None
                mains += 1
                check_wording(number, main_text, "main" if section["kind"] == "core" else "edge", profile, warnings)
            elif probe and mains and section["kind"] == "core":
                indent = len(probe.group(1))
                if base_indent is None:
                    base_indent = indent
                section["probe_lines"] = section.get("probe_lines", 0) + 1
                if indent > base_indent:
                    section["sub_probes"] = section.get("sub_probes", 0) + 1
                elif not BRANCH_TAG.match(probe.group(2).strip()):
                    probes_for_current += 1
                    section["top_probes"] = section.get("top_probes", 0) + 1
                check_wording(number, probe.group(2), "probe", profile, warnings)
            elif probe:
                check_wording(number, probe.group(2), "edge", profile, warnings)
            elif line.strip().startswith(">"):
                check_wording(number, line.strip().lstrip(">").strip(), "script", profile, warnings)
        if probes_for_current > profile["max_probes_per_main_question"]:
            warnings.append(("format.question-count", f"guide: last question in '{section['title']}' has {probes_for_current} first-level probes; maximum is {profile['max_probes_per_main_question']}"))
        if section["kind"] == "core":
            core_questions += mains
            core_minutes += section.get("minutes", 0)
        if mains > profile["max_main_questions_per_module"]:
            warnings.append(("format.question-count", f"guide: {section['title']} has {mains} main questions; maximum is {profile['max_main_questions_per_module']}"))
        elif mains > 2:
            warnings.append(("format.question-count", f"guide: {section['title']} has {mains} main questions; concise target is 1-2"))

    per_line = max(0.5, profile.get("probe_minutes_per_line", 1.5))
    for section in core_sections:
        minutes = section.get("minutes", 0)
        lines = section.get("probe_lines", 0)
        if not minutes:
            continue
        needed = max(3, math.ceil(minutes / per_line))
        top = section.get("top_probes", 0)
        if lines < needed:
            warnings.append(("format.question-count", f"guide: '{section['title']}' is {minutes} minutes but prepares only {lines} probe lines; at about {per_line} min per line it needs about {needed}"))
        elif top > minutes:
            warnings.append(("format.question-count", f"guide: '{section['title']}' has {top} first-level probes for {minutes} minutes; more branches than can be used"))

    if core_minutes:
        low, high = profile["minutes"].get(interview_format, profile["minutes"]["user-depth"])
        most = max(1, core_minutes // low)
        least = max(1, math.ceil(core_minutes / high))
        if core_questions > most:
            warnings.append(("format.question-count", f"guide: {core_questions} core main questions in {core_minutes} core minutes; {interview_format} budget is {least}-{most}"))
        elif core_questions < least:
            warnings.append(("format.question-count", f"guide: only {core_questions} core main questions in {core_minutes} core minutes; {interview_format} budget is {least}-{most}"))
    colloquial = len(re.findall(r"弄", text))
    if colloquial >= 3:
        warnings.append(("format.natural-wording", f"guide: '弄' appears {colloquial} times; write the action instead (迁移、导入、操作、设置)"))
    if len(numbers) != len(set(numbers)):
        warnings.append(("format.numbering", "guide: question numbers repeat; number questions continuously across modules"))


def main(argv: list[str]) -> int:
    allow_template = "--template" in argv
    draft = "--draft" in argv
    profile_path = DEFAULT_PROFILE
    args: list[str] = []
    skip = False
    for index, item in enumerate(argv[1:], start=1):
        if skip:
            skip = False
            continue
        if item == "--profile" and index + 1 < len(argv):
            profile_path = Path(argv[index + 1])
            skip = True
        elif item not in ("--template", "--draft"):
            args.append(item)
    if len(args) not in (1, 2):
        print("usage: lint_guide.py brief.md [guide.md] [--template] [--draft] [--profile profile.yaml]", file=sys.stderr)
        return 2
    profile = load_profile(profile_path)
    errors: list[tuple[str, str]] = []
    warnings: list[tuple[str, str]] = []
    check_brief(read(args[0]), errors, warnings)
    if len(args) == 2:
        check_guide(read(args[1]), errors, warnings, profile, allow_template=allow_template, draft=draft)
    for rule_id, message in warnings:
        print(f"warning [{rule_id}]: {message}")
    for rule_id, message in errors:
        print(f"error [{rule_id}]: {message}")
    if errors:
        return 1
    print("interview guide checks passed" + (" with warnings" if warnings else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
