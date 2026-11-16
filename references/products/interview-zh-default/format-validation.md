# 中文默认产品格式规则

这些规则约束正式产物的内容和版式，不改变研究判断、伦理或证据边界。

| rule_id | 检查 | severity |
|---|---|---|
| `format.brief-required` | 简报包含目标或应用、SRQ、形式与方法、对象资格、样本、记录边界和时间预算 | warning |
| `format.brief-minimal` | 简报只保留研究和执行必需信息，不包含过程日志、方法教程或重复提醒 | warning |
| `format.guide-required` | 大纲包含开场同意、模块时长、关键主问、必要追问和总结 | warning |
| `format.guide-minimal` | 大纲只保留主持人要说、要问或必须据此转向的内容；必问/可删和删减顺序放在简报 | warning |
| `format.guide-closing` | 大纲包含未覆盖内容、受访者提问和停止记录提示；有已确认的后续安排时再说明 | warning |
| `format.time-range` | 模块标题写时长，如“## 二、换机过程（15mins）”；各模块时长合计不超过总时长 | warning |
| `format.question-count` | 核心主问题数量、每题追问、追问密度、分支和座谈会轮流题计时符合 [工作流](workflow.md) 的内容预算 | warning |
| `format.numbering` | 主问题用不重复的【短标签】标识；如果改用数字编号，全篇连续 | warning |
| `format.natural-wording` | 问题读出来像主持人说话：没有书面腔、AI 腔和客服腔；主问题一口气能读完 | warning |
| `format.naming` | 文件名使用日期、项目简称、文档类型和两位版本号 | warning |
