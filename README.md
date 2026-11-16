# M-interview

M-interview 是中文定性研究访谈设计 Skill。它从研究目标和业务决策出发，选择访谈形式和方法，生成访谈简报与现场访谈大纲，并用验证规则检查证据边界、伦理、问法和交付格式。

## 支持的工作

- 用户深访、专家访谈和座谈会。
- 访谈简报、现场访谈大纲和按需的定向访前案头调研。
- 访谈大纲审核、修改、快速提问和方法咨询。
- 中文默认产品，以及通过 overlay 替换团队的写作、格式和附加验证。

## 兼容性状态

当前 `0.4.3` 不声明合同兼容性。`contracts/manifest.json` 锁定当前合同 revision；修改合同、验证规则或 conformance 用例后，必须重新评测。

现有方法卡还没有按模块合同的十个章节改写，暂不声明模块合同兼容性；新增或升级的方法卡必须遵守模块合同并通过 modules 评测。

## 目录

```text
m-interview/
├── SKILL.md
├── product.yaml
├── contracts/
├── references/
│   ├── services/
│   ├── modules/
│   ├── products/interview-zh-default/
│   ├── products/interview-en-minimal/
│   └── overlays/
├── evals/
├── scripts/
└── docs/ARCHITECTURE.md
```

安装时目录名必须是 `m-interview`，与 `SKILL.md` 中的 `name` 一致。

## 检查

```bash
python scripts/check_repo.py
python scripts/lint_guide.py brief.md guide.md            # 草稿加 --draft
python scripts/run_evals.py list
python scripts/contract_manifest.py check
python scripts/check_publish.py --all --denylist <内部词表> --corpus <私有材料目录>   # 发布前
```

行为评测需要另行运行真实模型。结构检查不替代行为评测。`check_publish.py` 检查内部词和从私有材料原样搬来的句子；词表和私有材料放在仓库外，脚本只读取它们。`lint_guide.py` 的问法检查（预设、将来意愿、是非问、AI 腔、术语）是启发式的，只提示可疑行。

贡献规则见 [CONTRIBUTING](CONTRIBUTING.md)。合同、官方验证规则或 `conformance` 用例变化后，必须更新 `contracts/manifest.json` 和 `CHANGELOG.md`。
