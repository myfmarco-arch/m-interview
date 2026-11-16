import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINT = ROOT / "scripts/lint_guide.py"
CHECK = ROOT / "scripts/check_repo.py"
PUBLISH = ROOT / "scripts/check_publish.py"


def run(*args):
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)


class ScriptTests(unittest.TestCase):
    def test_repository_check(self):
        result = run(str(CHECK))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_lint_catches_hand_card_problems(self):
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "brief.md"
            guide = Path(directory) / "guide.md"
            brief.write_text("SRQ 研究性质 方法 同意 录音 时间", encoding="utf-8")
            guide.write_text("# 主持人注意\n待回头\n", encoding="utf-8")
            result = run(str(LINT), str(brief), str(guide))
            self.assertEqual(result.returncode, 1)
            self.assertIn("guide.no-placeholder", result.stdout)
            self.assertIn("warning [format.guide-minimal]", result.stdout)

    def test_lint_has_no_page_or_line_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "brief.md"
            guide = Path(directory) / "guide.md"
            brief.write_text("SRQ 研究性质 方法 同意 录音 时间", encoding="utf-8")
            guide.write_text("收尾\n" + "问题\n" * 200, encoding="utf-8")
            result = run(str(LINT), str(brief), str(guide))
            self.assertEqual(result.returncode, 0)
            self.assertNotIn("format.guide-length", result.stdout)

    def test_lint_catches_time_overflow(self):
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "brief.md"
            guide = Path(directory) / "guide.md"
            brief.write_text("SRQ 研究性质 方法 同意 录音 时间", encoding="utf-8")
            guide.write_text("时长：60 分钟\n## 开场（第 0–30 分钟）\n## 模块（第 30–60 分钟）\n## 收尾（第 60–70 分钟）", encoding="utf-8")
            result = run(str(LINT), str(brief), str(guide))
            self.assertEqual(result.returncode, 1)
            self.assertIn("design.time-budget", result.stdout)

    def test_lint_catches_bracket_placeholder(self):
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "brief.md"
            guide = Path(directory) / "guide.md"
            brief.write_text("SRQ 研究性质 方法 同意 录音 时间", encoding="utf-8")
            guide.write_text("## 收尾（第 50–60 分钟）\n请问 [主题]？", encoding="utf-8")
            result = run(str(LINT), str(brief), str(guide))
            self.assertEqual(result.returncode, 1)
            self.assertIn("guide.no-placeholder", result.stdout)

    def test_lint_catches_process_text(self):
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "brief.md"
            guide = Path(directory) / "guide.md"
            brief.write_text("SRQ 研究性质 方法 同意 录音 时间", encoding="utf-8")
            guide.write_text("## 收尾（第 50–60 分钟）\n下面是整理后的版本\n1. **还有什么重要内容没有谈到？**", encoding="utf-8")
            result = run(str(LINT), str(brief), str(guide))
            self.assertEqual(result.returncode, 0)
            self.assertIn("warning [format.guide-minimal]", result.stdout)

    def test_lint_warns_on_three_main_questions(self):
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "brief.md"
            guide = Path(directory) / "guide.md"
            brief.write_text("SRQ 研究性质 方法 同意 录音 时间", encoding="utf-8")
            guide.write_text(
                "## 模块（第 0–30 分钟）\n"
                "1. **问题一？**\n2. **问题二？**\n3. **问题三？**\n"
                "## 收尾（第 30–60 分钟）\n1. **还有什么重要内容没有谈到？**",
                encoding="utf-8",
            )
            result = run(str(LINT), str(brief), str(guide))
            self.assertEqual(result.returncode, 0)
            self.assertIn("format.question-count", result.stdout)

    def test_lint_accepts_english_product_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "brief.md"
            guide = Path(directory) / "guide.md"
            brief.write_text(
                "Research questions SRQ\nResearch nature\nMethod\nConsent\nTime",
                encoding="utf-8",
            )
            guide.write_text(
                "Duration: 60 minutes\n## Opening (minutes 0-5)\n"
                "## Closing (minutes 50-60)\n1. **What did we miss?**",
                encoding="utf-8",
            )
            result = run(str(LINT), str(brief), str(guide))
            self.assertEqual(result.returncode, 0, result.stdout)

    def lint_guide(self, guide_text, *flags):
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "brief.md"
            guide = Path(directory) / "guide.md"
            brief.write_text("SRQ 研究性质 方法 同意 录音 时间 样本\n| 模块 | SRQ | 时间 |", encoding="utf-8")
            guide.write_text(guide_text, encoding="utf-8")
            return run(str(LINT), str(brief), str(guide), *flags)

    def test_lint_reads_duration_from_template_header(self):
        result = self.lint_guide(
            "# 大纲\n\n用户深访｜60 分钟｜换机用户｜v01｜2026-11-16\n\n"
            "## 开场（第 0–10 分钟）\n1. **先说说您现在用的手机。**\n"
            "## 换机（第 10–70 分钟）\n2. **请从头讲讲那次换机。**\n"
            "## 收尾（第 70–80 分钟）\n3. **还有什么我们没聊到的？**\n"
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("design.time-budget", result.stdout)

    def test_lint_counts_only_core_questions_by_minutes(self):
        core = "".join(f"{n}. **请讲讲第 {n} 件事。**\n" for n in range(2, 12))
        result = self.lint_guide(
            "用户深访｜60 分钟｜用户｜v01\n## 开场（第 0–5 分钟）\n1. **先说说您的情况。**\n"
            "## 核心（第 5–55 分钟）\n" + core +
            "## 收尾（第 55–60 分钟）\n12. **还有什么我们没聊到的？**\n13. **您有什么想问我们的吗？**\n"
        )
        self.assertIn("10 core main questions in 50 core minutes", result.stdout)

    def test_lint_flags_wording_problems(self):
        result = self.lint_guide(
            "用户深访｜60 分钟｜用户｜v01\n## 开场（第 0–5 分钟）\n1. **先说说您的情况。**\n"
            "## 核心（第 5–25 分钟）\n2. **能否请您分享一下换机过程中的整体体验？**\n"
            "## 核心二（第 25–45 分钟）\n3. **以后您会不会愿意为 AI 功能多付钱？**\n"
            "   - 新系统是不是很方便？\n"
            "## 核心三（第 45–55 分钟）\n4. **您对负一屏满意吗？**\n"
            "## 收尾（第 55–60 分钟）\n5. **还有什么我们没聊到的？**\n"
        )
        for rule in ("format.natural-wording", "question.no-hypothetical", "question.no-leading", "question.open-form"):
            self.assertIn(rule, result.stdout)

    def test_lint_draft_slots_only_in_draft(self):
        guide = (
            "用户深访｜60 分钟｜用户｜v01\n## 开场（第 0–5 分钟）\n"
            "> 我们会录音，只用于【执行前补：研究用途】。\n1. **先说说您的情况。**\n"
            "## 核心（第 5–55 分钟）\n2. **请从头讲讲最近一次换机。**\n"
            "## 收尾（第 55–60 分钟）\n3. **还有什么我们没聊到的？**\n"
        )
        self.assertEqual(self.lint_guide(guide).returncode, 1)
        self.assertEqual(self.lint_guide(guide, "--draft").returncode, 0)

    def test_lint_flags_thin_probe_density(self):
        result = self.lint_guide(
            "用户深访｜60 分钟｜用户｜v01\n## 开场（第 0–5 分钟）\n1. **先说说您的情况。**\n"
            "## 核心（第 5–45 分钟）\n2. **请从头讲讲最近一次换机。**\n   - 当时先发生了什么？\n"
            "## 收尾（第 45–60 分钟）\n3. **还有什么我们没聊到的？**\n"
        )
        self.assertIn("prepares only 1 probe lines", result.stdout)

    def test_lint_reads_team_format(self):
        guide = (
            "用户深访｜60mins｜换机用户｜v01\n"
            "## 一、开场热身（5mins）\n#### **解释访谈目的和流程**\n- 您好，访谈大约 1 小时。\n"
            "## 二、换机过程（30mins）\n*接下来，我们聊聊换机的过程*\n"
            "#### 【换机过程】请您帮我回忆一下，这次换机都做了哪些事？\n"
            + "".join(f"- 追问{n}是什么情况？\n" for n in range(20)) +
            "- [有人帮忙]：是谁帮的？\n"
            "## 三、使用体验（30mins）\n#### 【习惯迁移】换机之后，哪些操作和原来不一样？\n"
            + "".join(f"- 追问{n}是怎么处理的？\n" for n in range(20)) +
            "## 四、总结（5mins）\n- 还有什么我们没聊到的？\n"
        )
        result = self.lint_guide(guide)
        self.assertIn("design.time-budget", result.stdout)
        self.assertIn("70 min", result.stdout)

    def test_lint_flags_forced_colloquial(self):
        result = self.lint_guide(
            "用户深访｜30mins｜用户｜v01\n## 一、开场热身（5mins）\n- 您好。\n"
            "## 二、换机过程（20mins）\n#### 【换机过程】照片是怎么弄过来的？\n"
            "- 当时是啥情况？\n- 最后谁拍板的？\n- 还有别的吗？\n"
            "## 三、总结（5mins）\n- 还有什么我们没聊到的？\n"
        )
        self.assertIn("forced colloquial", result.stdout)

    def test_lint_flags_repeated_numbers(self):
        result = self.lint_guide(
            "用户深访｜30 分钟｜用户｜v01\n## 开场（第 0–5 分钟）\n1. **先说说您的情况。**\n"
            "## 核心（第 5–25 分钟）\n1. **请从头讲讲最近一次换机。**\n"
            "## 收尾（第 25–30 分钟）\n1. **还有什么我们没聊到的？**\n"
        )
        self.assertIn("format.numbering", result.stdout)

    def test_lint_accepts_templates(self):
        for rel in ("references/products/interview-zh-default", "references/products/interview-en-minimal"):
            result = run(str(LINT), str(ROOT / rel / "brief-template.md"), str(ROOT / rel / "guide-template.md"), "--template")
            self.assertEqual(result.returncode, 0, result.stdout)


    def test_lint_main_question_pairing(self):
        def guide(main):
            return (
                "用户深访｜30mins｜用户｜v01\n## 一、开场热身（5mins）\n- 您好。\n"
                f"## 二、使用情况（20mins）\n#### 【最近一次】{main}\n"
                + "".join(f"- 追问{n}怎么处理的？\n" for n in range(14)) +
                "## 三、总结（5mins）\n- 还有什么我们没聊到的？\n"
            )
        allowed = self.lint_guide(guide("最近一次用负一屏是什么时候？当时是什么情况？"))
        self.assertNotIn("question.single-task", allowed.stdout)
        unrelated = self.lint_guide(guide("最近一次用负一屏是什么时候？您觉得它好用吗？"))
        self.assertIn("question.single-task", unrelated.stdout)

    def focus_group(self, header, module):
        return (
            f"{header}\n## 一、开场热身（10mins）\n- 各位好。\n"
            f"{module}"
            "## 三、总结（5mins）\n- 还有什么我们没聊到的？\n"
        )

    def test_lint_focus_group_round_time(self):
        module = (
            "## 二、各自情况（20mins）\n"
            "#### 【最近一次】请讲讲最近一次在家用智能设备的情况。（轮流）\n- 当时家里还有谁在？\n- 后来怎么处理的？\n"
            "#### 【控制方式】平时都是怎么控制这些设备的？（轮流）\n- 哪样最常用？\n"
            "#### 【设备由来】家里第一样设备是怎么来的？（轮流）\n- 当时是谁决定的？\n"
        )
        result = self.lint_guide(self.focus_group("座谈会｜90mins｜8人｜用户｜v01", module))
        self.assertIn("round questions; with 8 people", result.stdout)
        self.assertNotIn("prepares only", result.stdout)

    def test_lint_focus_group_round_probes(self):
        module = (
            "## 二、各自情况（20mins）\n"
            "#### 【最近一次】请讲讲最近一次在家用智能设备的情况。（轮流）\n"
            + "".join(f"- 追问{n}是什么情况？\n" for n in range(6))
        )
        result = self.lint_guide(self.focus_group("座谈会｜90mins｜6人｜用户｜v01", module))
        self.assertIn("round question", result.stdout)
        self.assertIn("at most 3", result.stdout)

    def test_lint_focus_group_needs_participant_count(self):
        module = "## 二、各自情况（20mins）\n#### 【最近一次】请讲讲最近一次的情况。（轮流）\n- 当时怎么处理的？\n"
        result = self.lint_guide(self.focus_group("座谈会｜90mins｜用户｜v01", module))
        self.assertIn("no participant count", result.stdout)

    def publish_check(self, content):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            corpus = Path(directory) / "private"
            repo.mkdir()
            corpus.mkdir()
            (corpus / "old-guide.md").write_text("请您回忆一下上次参加星河项目内部评审时，团队是怎么分工推进的？\n", encoding="utf-8")
            terms = Path(directory) / "terms.txt"
            terms.write_text("# 内部词\n星河项目\n", encoding="utf-8")
            (repo / "guide.md").write_text(content, encoding="utf-8")
            git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com"]
            subprocess.run(git[:3] + ["init", "-q"], check=True)
            subprocess.run(git + ["add", "."], check=True)
            subprocess.run(git + ["commit", "-q", "-m", "x"], check=True)
            return run(str(PUBLISH), "--repo", str(repo), "--all", "--denylist", str(terms), "--corpus", str(corpus))

    def test_publish_check_passes_clean_text(self):
        result = self.publish_check("请您帮我回忆一下最近一次换手机的经过。\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_publish_check_flags_internal_term(self):
        result = self.publish_check("这次访谈来自星河项目。\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("term", result.stdout)

    def test_publish_check_flags_copied_line(self):
        result = self.publish_check("请您回忆一下上次参加内部评审时，团队是怎么分工推进的？\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("copy", result.stdout)


if __name__ == "__main__":
    unittest.main()
