# 核心验证规则

以下规则适用于所有访谈和所有产品。问法规则同时检查主问题和追问；只写“主问题”的规则只检查主问题。

| rule_id | 检查 | severity |
|---|---|---|
| `evidence.no-prevalence` | 不把少量访谈的比例、频率、排序或预测写成总体结论 | error |
| `evidence.narrative-boundary` | 不把自述自动改写为客观事实；行为题优先使用现场证据 | warning |
| `evidence.no-case-copy` | 不复制历史项目的品牌、样本、指标和具体问法 | warning |
| `evidence.rating` | 访谈中打分只用来引出理由和前后变化；打分后必须追问理由；不汇总均值、不算比例 | warning |
| `question.single-task` | 一个主问题只做一件事；回忆、比较、评价分开问。可以“时间或事件锚点 + 开放叙述”连问，两句必须指同一件事 | warning |
| `question.no-leading` | 问题不带预设前提、倾向性评价词或答案选项，例如“是不是很方便”“最吸引您的是哪里” | warning |
| `question.no-hypothetical` | 用户深访和座谈会的主问题不问将来意愿或假设情境；假设性追问和取舍练习的回答只作态度材料，不作需求或行为证据；专家的反事实追问不受此限 | warning |
| `question.open-form` | 主问题用开放问法；是非问只用于确认资格、确认经历或进入分支 | warning |
| `question.order` | 同一主题先宽后窄、先自发后提示；刺激物、品牌和研究员分类放在受访者自述之后 | warning |
| `question.knowledge-boundary` | 研究员术语不写成受访者问题的前提 | warning |
| `question.experience-required` | 不要求受访者评价自己没有经历过的行为 | error |
| `question.fact-first` | 用户深访和座谈会先具体经历，再进入观点和评价；专家访谈可概念先行，但重要判断必须追证据 | warning |
| `question.case-required` | 行为或经历模块至少有一个具体事件、案例或现场证据 | warning |
| `question.contradiction` | 前后差异并列呈现，追问场景，不要求选择唯一真实答案 | warning |
| `question.habit-choice` | 问“为什么选择”前先区分有意选择和习惯 | info |
| `ethics.consent` | 简报和开场包含用途、记录、匿名、跳过和退出；跳过和退出默认写明；方案要求时说明发起方；有记录时，收尾说明停止记录 | error |
| `ethics.no-invention` | 未确认的研究用途、记录方式、匿名边界或发起方身份不得被模型补写成事实；未提供后续安排时不虚构具体安排；生效 overlay 的团队标准同意信息视为已确认 | error |
| `ethics.sensitive-exit` | 敏感问题前提供拒答出口 | warning |
| `ethics.refusal-limit` | 明确拒绝后最多降级一次，再拒绝就停止 | error |
| `ethics.minor` | 受访者未满 18 周岁时，简报写明监护人同意和在场方式；不问收入、恋爱、健康等敏感内容，除非研究目标必需且监护人已同意 | error |
| `ethics.distress` | 涉及敏感话题、特殊人群或可能引起情绪波动的经历时，简报写明受访者明显不适时的处理：暂停、确认是否继续、改约或结束；中途结束是否照发礼金属于后续安排，需确认 | warning |
| `guide.no-placeholder` | `ready` 大纲正文没有待定、待确认、TODO 或空位；`draft` 大纲只允许在开场使用“【执行前补：……】”空位 | error |
| `guide.fielded-freeze` | 跨场次冻结必问、核心 SRQ 和关键分支；修改时记录版本、原因和生效场次 | warning |
