# 组合与覆盖合同

`m-interview-contract-v1` 定义产品、overlay 和 local.yaml 的合并方式。

## 可覆盖范围

| 对象 | 允许操作 |
|---|---|
| 产品 workflow、writing、brief_format、guide_format、naming | `replace` 或 `extend` |
| 研究设计服务 | 只允许 `extend` |
| 方法和知识模块 | `add` 或 `replace` |
| 适配器 | `add`，可指定默认值 |
| 验证规则 | 只允许 `add` |
| 团队标准同意信息 `ethics_defaults` | 只允许 `add` |
| 合同、官方验证、产物字段语义 | 不允许覆盖 |

## overlay.yaml

```yaml
schema_version: 2
id: team-custom
description: 团队访谈规范
targets: interview-zh-default
overrides:
  writing:
    mode: extend
    file: writing.md
  guide_format:
    mode: replace
    file: guide-format.md
validation:
  add:
    - file: validation/team-checks.md
      trigger: 每次交付前
ethics_defaults:
  mode: add
  file: ethics-defaults.md
evals:
  - evals/cases.yaml
```

`file` 相对于 overlay.yaml 所在目录；`targets` 必须与产品 id 一致；所有覆盖项必须显式写 `mode`。

## 团队标准同意信息

`ethics_defaults` 指向一份团队已经审定的同意信息：发起方说明方式、研究用途、记录方式、匿名边界、跳过和退出、礼金等后续安排，可附标准话术。启用该 overlay 时，这些信息视为已确认，可以直接写进开场和收尾。

- 只能写团队已经审定的事实，不得写“视情况”“待定”。
- 用户在请求里给出不同信息时，以用户为准。
- 简报的“记录与隐私”注明信息来自团队标准。
- 它不能关闭 `ethics.consent` 或任何官方验证规则。

## 合并语义

- `replace`：完整替换该产品文件。
- `extend`：保留默认内容，再追加 overlay 内容；不写删除语义时，不得静默删除默认规则。
- 多个 overlay 按 product.yaml 中的顺序合并，后者覆盖前者的产品偏好。
- 服务只允许扩展，验证只允许新增。

## local.yaml

local.yaml 默认不提交。它可以设置 `product`、登记本地产品、启用 overlay 和追加验证。它不能修改合同或关闭官方验证。
