#!/usr/bin/env python3
"""Check text before it is published: internal terms and lines copied from private material.

The term list and the private material stay outside the repository. This script only
reads them; nothing from them is written into the repository.

Usage:
  python3 scripts/check_publish.py --all --corpus <private-dir> [--denylist terms.txt]
  python3 scripts/check_publish.py --range origin/main..HEAD --corpus <private-dir>

Exit code 1 when a term is found or a line is too similar to the private material.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".txt", ".json", ".py"}
SHINGLE = 6


def normalize(text: str) -> str:
    """Keep only CJK characters, letters and digits, lowercased."""
    text = re.sub(r"`[^`]*`", "", text)
    return "".join(ch.lower() for ch in text if ch.isalnum())


def shingles(text: str) -> set[str]:
    return {text[i:i + SHINGLE] for i in range(max(0, len(text) - SHINGLE + 1))}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


def lines_from_tree(repo: Path) -> list[tuple[str, int, str]]:
    found = []
    for rel in git(repo, "ls-files").split("\n"):
        path = repo / rel
        if not rel or path.suffix not in TEXT_SUFFIXES or not path.is_file():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            found.append((rel, number, line))
    return found


def lines_from_range(repo: Path, revision_range: str) -> list[tuple[str, int, str]]:
    found = []
    current, number = "", 0
    for line in git(repo, "diff", "--unified=0", "--no-color", revision_range).splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else ""
        elif line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            number = int(match.group(1)) if match else 0
        elif line.startswith("+") and current:
            if Path(current).suffix in TEXT_SUFFIXES:
                found.append((current, number, line[1:]))
            number += 1
    return found


def load_terms(path: Path | None) -> list[str]:
    if not path:
        return []
    terms = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(line)
    return terms


def load_allowlist(path: Path | None) -> set[str]:
    if not path or not path.exists():
        return set()
    return {normalize(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")}


def load_corpus(directories: list[Path]) -> tuple[list[tuple[str, str, str]], dict[str, list[int]]]:
    sentences: list[tuple[str, str, str]] = []
    index: dict[str, list[int]] = {}
    for directory in directories:
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.suffix not in {".md", ".txt"}:
                continue
            for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                for part in re.split(r"(?<=[。！？?!；;])", raw):
                    norm = normalize(part)
                    if len(norm) < SHINGLE:
                        continue
                    sentence_id = len(sentences)
                    sentences.append((path.name, part.strip(), norm))
                    for gram in shingles(norm):
                        index.setdefault(gram, []).append(sentence_id)
    return sentences, index


def best_match(norm: str, sentences, index) -> tuple[float, float, str, str]:
    grams = shingles(norm)
    if not grams:
        return 0.0, 0.0, "", ""
    hits = Counter()
    covered = 0
    for gram in grams:
        ids = index.get(gram)
        if ids:
            covered += 1
            hits.update(set(ids))
    coverage = covered / len(grams)
    best_ratio, best_file, best_text = 0.0, "", ""
    for sentence_id, _ in hits.most_common(5):
        name, text, other = sentences[sentence_id]
        ratio = SequenceMatcher(None, norm, other).ratio()
        if ratio > best_ratio:
            best_ratio, best_file, best_text = ratio, name, text
    return coverage, best_ratio, best_file, best_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--all", action="store_true", help="check every tracked text file")
    scope.add_argument("--range", help="check only lines added in this git revision range, e.g. origin/main..HEAD")
    parser.add_argument("--repo", type=Path, default=ROOT, help="repository to check (default: this skill)")
    parser.add_argument("--denylist", type=Path, help="file with one internal term per line (kept outside the repo)")
    parser.add_argument("--corpus", type=Path, action="append", default=[], help="directory of private material (kept outside the repo)")
    parser.add_argument("--allowlist", type=Path, help="lines that are accepted even if they match the corpus")
    parser.add_argument("--min-chars", type=int, default=15, help="ignore lines shorter than this after normalizing")
    parser.add_argument("--threshold", type=float, default=0.75, help="flag lines whose similarity reaches this value")
    args = parser.parse_args()

    for directory in args.corpus:
        if not directory.is_dir():
            print(f"corpus directory not found: {directory}", file=sys.stderr)
            return 2
    lines = lines_from_tree(args.repo) if args.all else lines_from_range(args.repo, args.range)
    terms = load_terms(args.denylist)
    allowed = load_allowlist(args.allowlist)
    sentences, index = load_corpus(args.corpus)

    term_hits, copy_hits = [], []
    seen = set()
    for rel, number, line in lines:
        lowered = line.lower()
        for term in terms:
            if term.lower() in lowered:
                term_hits.append((rel, number, term, line.strip()))
        norm = normalize(line)
        if not sentences or len(norm) < args.min_chars or norm in allowed or norm in seen:
            continue
        seen.add(norm)
        coverage, ratio, source, text = best_match(norm, sentences, index)
        score = max(ratio, coverage if coverage >= 0.9 else 0.0)
        if score >= args.threshold:
            copy_hits.append((score, rel, number, line.strip(), source, text))

    for rel, number, term, line in term_hits:
        print(f"term   {rel}:{number}  '{term}'  {line[:100]}")
    for score, rel, number, line, source, text in sorted(copy_hits, reverse=True):
        print(f"copy   {score:.2f}  {rel}:{number}  {line[:90]}")
        print(f"       ≈ {source}: {text[:90]}")
    checked = f"{len(lines)} lines checked"
    if term_hits or copy_hits:
        print(f"publish check failed: {len(term_hits)} term hits, {len(copy_hits)} similar lines ({checked})")
        return 1
    print(f"publish check passed ({checked})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
