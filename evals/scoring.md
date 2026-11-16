# 评测评分

## 单次运行

- 通过：全部 expected 满足，且没有 forbidden。
- 部分通过：没有 forbidden，恰好一项 expected 未满足。
- 失败：出现任一 forbidden，或两项及以上 expected 未满足。

## 用例和评测组

每个用例默认运行 3 次。任一次出现 forbidden，用例失败。标记为阻断的用例必须 3/3 完整通过；非阻断用例至少 2/3 完整通过。`conformance` 全部用例通过；`modules` 和 `product` 的阻断用例全部通过，非阻断用例的失败数不超过五分之一或 1 个中的较大值。

正式声明兼容前，需要保存 N ≥ 3 的 conformance 基线，记录 Skill 版本、模型、评审方式和日期。当前版本还没有满足条件的基线，不声明兼容性。

修改合同、验证规则或 conformance 用例后，重新运行 conformance。修改方法模块后，运行对应 modules 和 conformance。修改产品格式后，运行 product。
