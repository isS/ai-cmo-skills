---
name: <skill-name>
description: <英文一句话触发描述，含关键词。例如：When to use — audit a website's technical SEO and return prioritized fixes. Use for "seo audit", "technical seo", "on-page seo".>
---

# <Skill 英文名 / 中文名>

一句话说明这个 skill 做什么。

## 用途 / Purpose

说明这个 skill 解决什么问题、在闭环中的位置。

## 触发时机 / When to Use

- 用户说「…」时
- 上游 skill 输出「…」时

## 前置上下文 / Required Context

- 先读取 `context/<xxx>.md`（如适用）
- 需要用户提供：…

## 输入 / Inputs

| 字段 | 必填 | 说明 |
|---|---|---|
| `<field>` | ✅/❌ | … |

## 输出 / Outputs

- 产出文件：`outputs/<skill-name>/<file>`
- 格式：JSON / Markdown
- 示例结构：…

## 验收项 / Acceptance Criteria

- [ ] …
- [ ] …
- [ ] …

## 执行步骤 / Steps

1. …
2. …

## 脚本 / Scripts

如有脚本，说明：

```bash
python scripts/<name>.py --help
```

依赖见 `scripts/requirements.txt`；凭据通过环境变量注入。

## 发布 / Publishing

如 skill 含写操作，说明审批节点与目标系统。
