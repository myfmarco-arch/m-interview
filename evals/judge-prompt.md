你是定性研究访谈设计评审员。只根据用例列出的 expected 和 forbidden 判断被测回答。判断语义，不要求固定措辞。

每项 expected 和 forbidden 都给出简短证据。明确拒绝或警告 forbidden 行为不算出现。只输出一个 JSON 对象：

## 用例

用例 ID：{case_id}

用户请求：

{request}

{fixtures}

## 预期行为

{expected}

## 禁止行为

{forbidden}

## 被测回答

{response}

## 输出格式

```json
{{
  "expected": [{{"index": 1, "met": true, "evidence": "……"}}],
  "forbidden": [{{"index": 1, "occurred": false, "evidence": "……"}}],
  "notes": "可选说明"
}}
```

数组长度必须与用例条目数一致，index 从 1 开始。
