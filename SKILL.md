---
name: m-interview
description: 设计、修改和审核定性研究的访谈简报与现场访谈大纲（访谈提纲、深访大纲、座谈会提纲、专家访谈提纲）。覆盖用户深访、专家访谈和座谈会，支持定向案头调研与中文默认产品。不用于转写、访谈分析、招募问卷或实时主持。
license: MIT
metadata:
  version: 0.5.0
  contract: m-interview-contract-v1
---

# M-interview

从研究目标选择访谈形式和方法，生成可直接使用的材料：

1. **访谈简报**：研究信息、设计依据、样本、执行边界和访前准备。主持人在访谈前读它。
2. **现场访谈大纲**：主持人现场要说的话和要问的问题。
3. **访前案头调研**（按需）：只保存会改变设计的公开信息。

正式文档只保留对研究或现场执行有用的内容。不要写读取过程、思考过程、方法解释、重复提醒、模型犹豫或未解决的内部标签。

## 渐进式工作流

### 1. 路由

先读 [任务路由](references/services/task-routing.md)，确定工作模式：`create`、`revise`、`audit`、`consult` 或 `quick-ask`。

再读 [产品清单](product.yaml) 的前 9 行，并查看根目录有没有 `local.yaml`。`product` 为 `interview-zh-default`、`overlays` 为空、没有 local.yaml，且用户没指定其他产品或 overlay 时，按本文件的路径读取；否则按产品清单、local.yaml 和 [覆盖合同](contracts/overlay-contract.md) 加载。

首轮只确认会改变形式、方法、伦理或现场执行的缺口。不要展示方法库，不要输出完整过程说明。

### 2. 判断交付状态

- **blocked**：缺少访谈类型、时长、对象资格或研究目标，或形式冲突、伦理冲突未解决。只列需要确认的项目，不生成大纲。
- **draft**：设计条件齐了，但开场需要的研究用途、记录方式或匿名边界未确认，也没有生效 overlay 提供的团队标准同意信息。交付完整简报和完整大纲草稿；未确认的项目只在开场写成“【执行前补：……】”空位，并在文档外集中问一次。设计上还有其他假设时，也停在 draft，假设写在文档外。
- **ready**：设计条件、方法、伦理和时间都已确认，验证中没有未通过的 error。交付正式文档。

不补写研究用途、记录方式、匿名边界、发起方或后续安排。跳过和退出默认写明。伦理信息的来源和例外见任务路由。

### 3. 选择方法

先读 [研究设计服务](references/services/research-design.md)、对应的形式模块（`references/modules/formats/` 下的 `user-depth.md`、`expert.md` 或 `focus-group.md`）和 [方法索引](references/modules/methods/index.md)。再按 SRQ 只读取必要的方法卡。每个 SRQ 一个主方法，选法见研究设计服务。方法卡按方法索引的“读取规则”使用。

案头调研：用户要求时直接做。满足 [案头调研服务](references/services/desk-research.md) 的启动条件时，在首轮澄清里提议一次，由用户决定。案头资料单独成文，用 [案头调研模板](references/products/interview-zh-default/desk-template.md)，不把搜索过程写入简报或大纲。

### 4. 生成材料

写问题前必读，生效 overlay 替换了的读替换后的文件：

- [访谈问题表达风格](references/products/interview-zh-default/writing.md)：团队写法和措辞。
- [问法设计](references/modules/knowledge/question-craft.md)：知识边界、追问、顺序与偏差。
- [工作流](references/products/interview-zh-default/workflow.md)：题量、追问密度和时间。
- [简报模板](references/products/interview-zh-default/brief-template.md) 和 [大纲模板](references/products/interview-zh-default/guide-template.md)。

必问/可删和删减顺序写在简报，不进大纲。

用户要专家外发版、访前告知或访后速记时，读 `references/adapters/` 下对应的 `expert-external.md`、`participant-notice.md` 或 `post-session-note.md`。

### 5. 验证与交付

验证规则：[核心规则](references/services/validation/core.md)；默认中文产品加 [格式规则](references/products/interview-zh-default/format-validation.md)；按形式加 `references/services/validation/` 下的 `user-depth.md`、`expert.md` 或 `focus-group.md`；有案头调研再加同目录的 `desk-research.md`；生效 overlay 新增的规则一并执行。

交付前逐题自检：

1. 这题对应哪个 SRQ？对应不上就删。
2. 问的是已经发生的事吗？主问题不问将来意愿或假设情境。
3. 有没有预设前提、倾向性词或答案选项？
4. 是不是一题一事？连问的两句是不是同一件事？是非问是否只用于确认或分支？
5. 受访者能不能直接回答？有没有具体的时间、场景或动作？
6. 读起来像不像团队写法？有没有 writing.md 列出的 AI 腔或硬加的口语？

再检查：形式匹配、时间合计、SRQ 覆盖、同意与退出、空位与占位符、必要分支、样本和版本命名。有代码环境时，可以运行 `scripts/lint_guide.py` 做启发式检查；它只提示可疑行，不替代逐题自检。

`error` 未通过时，不交付 `ready` 状态的大纲。问法类 warning（`question.*`）在生成时直接改掉，不留到交付说明里；审核别人的大纲时照常列出。验证结果不写进正式文档；交付时在文档外用一两句话说明仍存在的 warning 和假设，没有就不写。

## 工作模式

- **create**：先判断状态，再生成简报、现场大纲和按需案头调研。
- **revise**：只修改用户指定范围；保留有效的问题标签和语义，记录版本与修改原因。版本号按 [命名规则](references/products/interview-zh-default/naming.md) 递增。
- **audit**：先检查提供的材料，按严重程度列问题，用户要求时再重写。没有材料时只给检查范围，不假装完成审核。
- **consult**：只回答形式、方法、前提、替代方案和结论边界，不强制生成文档。
- **quick-ask**：最多确认一个最影响问法的条件，直接给问题和必要分支。

## 三类形式

- **用户深访**：个人经历、行为路径、选择、放弃、替代和具体案例。
- **专家访谈**：先定用途（学做法、拼规划、看格局、评技术、验假设、内部对齐），再按用途取证。
- **座谈会**：个人表达、群体差异、互动、刺激物反应、排序和共创。先个人、后群体；座谈会不能替代多次个人深访。

自定义或混合形式见任务路由。

## 规则合并

```text
研究事实、伦理和证据边界
> 用户已确认的任务要求
> 生效 overlay
> 默认产品配置
> 方法模块和案例
```

合同和官方验证规则不能被覆盖。overlay 只能替换或扩展产品偏好，新增服务、方法、验证规则和团队标准同意信息，不能关闭核心规则。

其余文件按需读取，不要一次加载全部资料。
