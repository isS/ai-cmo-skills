# AGENTS.md — 编排指南 / Orchestration Guide

本文件面向**运行这些 skills 的 AI Agent**，说明 skill 之间如何组合、共享上下文如何工作、以及每个 skill 的契约（输入/输出/验收）。

## 1. 共享上下文层 / Shared Context Layer

所有 skill 在开始前，必须先读取 `context/` 中**相关**的文档（按需，不必全读）：

| 文档 | 谁需要读 |
|---|---|
| `context/product-information.md` | website-research、seo-audit、content-brief、blog-post、linkedin-post、competitor-analysis |
| `context/brand-voice.md` | blog-post、linkedin-post、content-brief、所有内容生产类 skill |
| `context/competitor-analysis.md` | content-gap、content-brief、blog-post、seo-audit |
| `context/content-strategy.md` | content-gap、content-brief、blog-post、weekly-growth-report |
| `context/marketing-strategy.md` | 所有战略决策类 skill |

规则：**如果 `context/` 中已有对应文档，优先以文档为准，不要重新推断。** 文档缺失时才主动采集补全。

## 2. Skill 契约 / Contract

每个 skill 的 `SKILL.md` 必须声明四件事：

- **Inputs（输入）**：期望用户/上游 skill 提供什么
- **Outputs（输出）**：产出什么、写到哪个文件/用什么格式
- **Acceptance Criteria（验收项）**：怎么算完成（checklist）
- **Scripts（脚本）**：可选，如何运行、依赖是什么

上游 skill 的输出应尽量**写入文件**（如 `outputs/<skill-name>/...`），供下游 skill 读取，形成可追溯的数据流。

## 3. 闭环流水线 / Closed Loop

推荐执行顺序（也对应一个完整营销迭代）：

```
[研究] website-research → competitor-analysis
  └─ 更新 context/product-information.md + context/competitor-analysis.md
[语气] brand-voice
  └─ 更新 context/brand-voice.md
[机会] seo-audit → content-gap
  └─ 产出 fix 清单 + 关键词机会清单
[生产] content-brief → blog-post / linkedin-post
  └─ 产出待审稿件到 outputs/
[发布] cms-publish（人工审批后）
  └─ 推送到 CMS / GitHub
[度量] weekly-growth-report
  └─ 从 GSC + GA4 归因 → 产出下周优先级 → 回到 [机会]
```

关键点：**每一步都有明确产物，且产物可被下一步消费**。审批节点（发布前）必须有人工确认。

## 4. 人工审批 / Human-in-the-loop

以下操作属于「写操作」，执行前必须两阶段确认：

- `cms-publish`：对外发布内容
- 任何覆盖 `context/` 共享文档的操作
- 任何对外发送消息（LinkedIn、邮件等）

## 5. 脚本约定 / Script Conventions

- 语言：Python 3.10+
- 依赖：尽量标准库；第三方依赖在 `scripts/requirements.txt` 中声明
- 凭据：通过环境变量读取，**绝不硬编码**（如 `GSC_CREDENTIALS`, `GA4_PROPERTY_ID`, `CMS_API_URL`, `CMS_API_TOKEN`）
- 输出：默认打印 JSON 到 stdout，便于 Agent 解析

## 6. 语言约定 / Language

- `name`、`description` 使用英文（保证跨 Agent 触发词匹配）
- SKILL.md 正文使用**中英双语**（英文为主、中文为辅）
