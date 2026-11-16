# 研究产物合同

`m-interview-contract-v1`。当前 revision 见 [manifest.json](manifest.json)。

## 产物链

```text
ResearchBrief → MethodPlan → SessionPlan → GuideSpec → Deliverable
      ↘ DeskResearch（可选）↗              ↘ ValidationResult ↙
```

## ResearchBrief

研究简报的最小字段：

| 字段 | 含义 |
|---|---|
| `decision` | 研究结果支持的业务决定或应用目的 |
| `research_questions` | SRQ 列表；每项是需要获得的知识，不是问句 |
| `object` | 研究对象、产品或议题 |
| `experience_stage` | 购买、使用、迁移、流失、组织流程等阶段 |
| `target_population` | 受访对象、资格、分群和排除条件 |
| `sample` | 场次、分群配额，以及不在样本里的人群和对结论的影响 |
| `comparisons` | 需要比较的对象、阶段或场景 |
| `constraints` | 时长、形式、刺激物、记录和执行限制 |
| `assumptions` | 尚未确认但不阻断设计的假设 |
| `interview_format` | `user-depth`、`expert`、`focus-group` 或未定义形式 |
| `duration_min` | 预计总分钟数 |
| `research_nature` | `explore`、`explain`、`evaluate` 或 `predict` |
| `ethics` | 同意、记录、匿名、发起方披露、敏感范围、跳过、退出和后续安排；每项注明来源：用户确认或生效 overlay 的团队标准 |

## MethodPlan

每个 SRQ 必须记录：证据类型、主方法、必要的辅助方法、证据链、可以得出和不能推出的结论，以及需要推翻的假设。辅助方法没有证据增益时不添加。

## SessionPlan

记录模块、对应 SRQ、时间范围、缓冲、必问和可跳过内容、删减顺序、必要分支、座谈会轮次、刺激物顺序、主持配置和分群。对应 SRQ、必问/可删和删减顺序在简报中呈现，不进入现场大纲。

## GuideSpec

GuideSpec 是现场大纲的内部语义对象。默认不单独交付，但在生成大纲前必须形成并完成校验：

```yaml
format: user-depth
duration_min: 60
modules:
  - id: purchase-path
    title: 本次购买经历
    time: 15-30
    research_questions: [SRQ-1]
    questions:
      - id: Q1
        priority: must
        main: 请回忆最近一次购买，从开始想到最后决定，讲一遍。
        probes:
          - 当时先发生了什么？
          - 看过哪些方案？
        branch: 若未购买，转问考虑后放弃的最近一次经历。
```

每个 SRQ 至少对应一个 `priority: must` 的核心问题；每个核心问题的 `research_questions` 不为空。问题 `id` 全篇唯一。现场大纲用不重复的【短标签】标识主问题；改用数字编号时全篇连续。

现场大纲的 Markdown 是 GuideSpec 的可读交付，不得改变 SRQ、模块时间、必问状态或分支语义。现场版本只呈现提问所需的最少信息，不呈现 MethodPlan 或 SessionPlan 的解释性内容，也不呈现必问状态。

## 交付状态

| 状态 | 可交付内容 | 禁止内容 |
|---|---|---|
| `blocked` | 阻断项和需要确认的问题 | 现场大纲、虚构的伦理事实 |
| `draft` | 完整简报和大纲草稿；未确认的研究用途、记录方式或匿名边界只在开场写成“【执行前补：……】”空位；其他假设写在文档外 | 称为可直接使用、把假设写入现场话术、在空位以外补写伦理信息 |
| `ready` | 访谈简报和现场访谈大纲；文档外用一两句说明仍存在的 warning 和假设 | 未确认事实、空位、过程日志、无用说明 |

阻断项和待确认问题在正式文档外呈现。设计条件（类型、时长、对象资格、目标）缺失时停在 `blocked`。只缺研究用途、记录方式或匿名边界时停在 `draft`：可以用生效 overlay 的团队标准同意信息补齐，不能用模型自拟的默认话术补齐。跳过和退出权利默认写明。发起方和后续安排未提供时，不点名发起方、不写具体安排，不阻断也不留空位。

## DeskResearch

可选案头调研记录信息需求、资料类型、来源和日期、对样本/方法/刺激物/问法的影响，以及待验证问题。公开表达不代表目标人群总体。

## Deliverable

默认包括访谈简报和现场访谈大纲。访前案头调研、专家外发版、访前告知和访后速记按需生成。案头调研单独成文，不并入现场大纲。ValidationResult 是内部对象，不作为正式文档交付，除非用户要求。

## ValidationResult

```yaml
rule_id: design.time-budget
severity: error
status: pass
message: 时间合计不超过预计时长
evidence: 简报第六节，合计 60 分钟
```

`status` 只能是 `pass`、`fail` 或 `not-applicable`。`error` 失败时不得交付可执行完整大纲。
