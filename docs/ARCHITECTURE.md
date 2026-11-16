# M-interview 架构

M-interview 借鉴 M-survey 的分层方式，把研究判断、方法知识和产品偏好分开。目标是：不同团队可以替换表达和版式，但不能绕过证据边界、伦理要求或产物字段语义。

## 分层

```text
SKILL.md
└── product.yaml
    ├── contracts/                 产物、模块、验证和覆盖合同
    ├── references/services/       路由、研究设计、案头调研和验证
    ├── references/modules/        访谈形式、方法和问法知识
    ├── references/adapters/       Markdown、外发版、访前告知、访后速记
    ├── references/products/       中文默认产品的工作流、写作和格式
    └── references/overlays/       团队的产品偏好、新增验证和团队标准同意信息
```

依赖方向是：合同 → 服务和模块 → 产品 → overlay。产品和 overlay 不能修改合同、官方验证规则、研究事实或证据状态。

## 研究产物

```text
ResearchBrief → MethodPlan → SessionPlan → GuideSpec → Deliverable
      ↘ DeskResearch（可选）↗              ↘ ValidationResult ↙
```

- `ResearchBrief` 说明决策、SRQ、对象、形式、时长、伦理和限制。
- `MethodPlan` 说明每个 SRQ 的证据类型、主方法、辅助方法和结论边界。
- `SessionPlan` 分配模块、时间、必问、可选、缓冲、跳题顺序和主持配置。
- `GuideSpec` 定义模块、问题、追问、分支、刺激物和收尾的语义。
- `Deliverable` 是按产品格式交付的简报、大纲或可选材料。

GuideSpec 是生成前的内部语义对象，不默认单独交付。Markdown 不得改变模块时间、必问状态或分支语义。必问状态、对应 SRQ 和删减顺序在简报中呈现，现场大纲保持简洁。

## 核心与场景附加规则

所有访谈都执行核心规则。用户深访、专家访谈和座谈会按触发条件加载各自的形式模块和验证规则。自定义或混合形式必须声明继承哪些形式规则；未声明时只执行核心规则并停在 draft，不能借用其他形式的例外。

乔哈里视窗是知识边界工具，不是独立访谈形式。它用于判断术语由谁掌握、问题应从概念还是具体事件开始。

## 评测和版本

`conformance` 评测检查所有产品必须保留的研究判断；`modules` 检查方法和服务；`product` 检查中文默认产品；`overlay` 检查团队覆盖。修改合同、验证规则或 conformance 用例时，必须更新合同 revision 和 manifest。

当前 0.3.0 不声明行为兼容性。结构检查通过不等于真实模型评测通过。`lint_guide.py` 的问法检查是启发式的，只用来提示可疑行。
