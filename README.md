# AI CMO Skills

An orchestratable marketing skill library for AI agents. Inspired by Okara's "AI CMO" architecture, this repo packages SEO, GEO/AI-search, content, social, publishing, and analytics capabilities as **composable, auditable skills** that any agent (Claude, Codex, Cursor, CodeBuddy, etc.) can install and call.

> 一个可编排、可审核、可发布的营销技能库。把 Okara 的「AI CMO」拆成一组能被任意 AI Agent 调用的 Skills，而不是单一大模型功能。

## 核心理念 / Core Idea

Okara 的价值不在「79 个 prompt」，而在三个设计。本仓库完整复刻这三点：

1. **共享上下文层 (Shared Context Layer)** — 所有 skill 先读取同一套 `context/` 文档（品牌语气、产品信息、竞品分析、内容策略、营销策略），防止跨渠道跑偏。
2. **标准输入/输出 + 验收项** — 每个 skill 有明确的 Inputs / Outputs / Acceptance Criteria，输出「可执行」的产物而非泛泛报告。
3. **闭环自动化 (Closed Loop)** — 研究 → 生成 → 人工审批 → 发布 → 数据归因 → 再优化。支持投放到 CMS / GitHub / LinkedIn，并从 Search Console / GA4 回收信号。

## 安装 / Install

### 方式一：`skills` CLI（vercel-labs/agent-skills）

```bash
npx skills add <your-github-user>/ai-cmo-skills
```

### 方式二：手动（Claude Code / Codex / CodeBuddy）

把本仓库 clone 到你的 skills 目录：

```bash
# Claude Code
git clone https://github.com/<your-github-user>/ai-cmo-skills.git ~/.claude/skills/ai-cmo-skills

# Codex
git clone https://github.com/<your-github-user>/ai-cmo-skills.git ~/.codex/skills/ai-cmo-skills

# CodeBuddy
git clone https://github.com/<your-github-user>/ai-cmo-skills.git ~/.codebuddy/skills/ai-cmo-skills
```

## 目录结构 / Structure

```
ai-cmo-skills/
├── README.md              # 本文件
├── AGENTS.md              # 编排指南：skill 如何组合成营销闭环
├── SKILL_TEMPLATE.md      # 新增 skill 的规范模板
├── LICENSE                # MIT
├── context/               # 共享上下文层（所有 skill 的输入源）
│   ├── brand-voice.md         # 品牌语气
│   ├── product-information.md # 产品信息
│   ├── competitor-analysis.md # 竞品分析
│   ├── content-strategy.md    # 内容策略
│   └── marketing-strategy.md  # 营销策略
└── skills/                # 10 个 MVP skill（每个含 SKILL.md + 可选 scripts/）
    ├── website-research/
    ├── brand-voice/
    ├── competitor-analysis/
    ├── seo-audit/
    ├── content-gap/
    ├── content-brief/
    ├── blog-post/
    ├── linkedin-post/
    ├── cms-publish/
    └── weekly-growth-report/
```

## 10 个 MVP Skills

| Skill | 能力域 | 脚本 | 作用 |
|---|---|---|---|
| `website-research` | 战略/上下文 | ✅ fetch_site.py | 抓取网站结构/元数据/内容，产出产品与市场情报 |
| `brand-voice` | 战略/上下文 | — | 提炼并固化品牌语气，供所有内容 skill 引用 |
| `competitor-analysis` | 战略/上下文 | ✅ fetch_competitors.py | 竞品定位、流量、关键词、内容策略对比 |
| `seo-audit` | SEO | ✅ seo_audit.py | 技术 SEO 审计，输出按影响力排序的可修复项 |
| `content-gap` | SEO | ✅ keyword_gap.py | 关键词缺口分析，找内容机会 |
| `content-brief` | 内容 | — | 产出结构化内容简报（目标/关键词/大纲/CTA） |
| `blog-post` | 内容 | — | 按 brief 生成可发布的博客长文 |
| `linkedin-post` | 社媒 | — | 生成 LinkedIn 帖子/系列 |
| `cms-publish` | 发布 | ✅ publish.py | 通用 CMS API 发布（WordPress/Webflow/自定义） |
| `weekly-growth-report` | 度量 | ✅ gsc_ga4_report.py | GSC + GA4 数据归因，产出周增长报告与下周优先级 |

## 推荐闭环 / Recommended Loop

```
网站 URL
  → website-research + competitor-analysis（共享上下文）
  → brand-voice 固化语气
  → seo-audit + content-gap 找机会
  → content-brief 出简报
  → blog-post / linkedin-post 生产内容
  → cms-publish 发布（人工审批后）
  → weekly-growth-report 归因 → 回到 seo-audit 进入下一轮
```

## 新增 Skill / Add a Skill

1. 复制 `SKILL_TEMPLATE.md` 到 `skills/<skill-name>/SKILL.md`
2. 填写 name（英文）、description（中英双语触发词）
3. 明确 Inputs / Outputs / Acceptance Criteria
4. 如需要脚本，放入 `skills/<skill-name>/scripts/` 并在 SKILL.md 中说明依赖与用法
5. 引用 `context/` 中的共享文档

## License

MIT
