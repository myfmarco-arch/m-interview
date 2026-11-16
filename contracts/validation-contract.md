# 验证合同

`m-interview-contract-v1` 使用三级严重程度：

| severity | 含义 | 交付行为 |
|---|---|---|
| `error` | 违反研究、伦理、证据或结构的硬约束 | 修复前不交付 `ready` 状态的可执行完整大纲 |
| `warning` | 重要风险，通常可在说明限制后继续 | 文档外说明限制或假设 |
| `info` | 建议或维护提示 | 按任务需要报告 |

规则只在一个规则文件中定义。评测用例通过 `targets` 引用规则 id。

验证先判断交付状态，再判断文档格式：

- `blocked`：缺少类型、时长、对象资格或目标，或存在形式冲突、伦理冲突；只交付阻断项。
- `draft`：设计条件齐全，但伦理信息未确认或仍有设计假设；可交付带“【执行前补：……】”空位的完整草稿，空位只在开场。
- `ready`：关键条件、方法、伦理和时间均通过，没有空位，才交付可直接使用的现场大纲。

## ValidationResult

```yaml
rule_id: question.single-task
severity: warning
status: pass
message: 每个主问题只承担一个主要任务
evidence: Q3 只有一个主问，比较内容放在追问
```

## 规则命名

使用 `<domain>.<rule>`，例如 `routing.blocking-info`、`design.time-budget`、`question.experience-required`、`ethics.consent`。

## 覆盖范围

- `always`：所有访谈和所有产品都必须执行。
- `when`：触发条件成立时执行，例如专家访谈、座谈会或案头调研。
- 产品规则只约束官方产品的格式，不得用 overlay 关闭核心研究判断或伦理规则。
- 未确认的研究用途、记录方式、匿名边界、发起方身份和后续安排不得由默认模板推断。生效 overlay 的团队标准同意信息视为已确认。

## 脚本检查

`scripts/lint_guide.py` 只做启发式检查。它的 warning 指向值得人工看一眼的行，不能代替逐题自检；它没有报错也不等于 error 级规则全部通过。
