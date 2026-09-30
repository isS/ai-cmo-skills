---
name: content-brief
description: When to use — produce a structured content brief (target, keywords, outline, CTA) ready to hand to a writer. Use for "content brief", "writing brief", "article brief", "content planning", "keyword brief". 生成可直接交给写手的内容简报（目标受众、关键词、大纲、CTA）。
---

# Content Brief / 内容简报

Turns "topic + audience + goal" into a structured content brief (search intent, keywords, H2/H3 outline, CTA) that serves as upstream input for blog-post / linkedin-post. / 将「主题 + 受众 + 目标」转化为结构化的内容简报（搜索意图、关键词、H2/H3 大纲、CTA），作为 blog-post / linkedin-post 的上游输入。

## 用途 / Purpose

In the closed loop, this skill sits between [opportunity] and [production]: it converts keyword/gap opportunities from seo-audit / content-gap into a writer-ready brief, keeping content aligned with search intent, brand voice, and competitive differentiation to reduce rework. / 本 skill 位于闭环中「机会」与「生产」之间：把 seo-audit / content-gap 产出的关键词/差距机会，转化为写手可直接执行的简报，保证内容与搜索意图、品牌语气、竞品差异对齐，减少返工。

## 触发时机 / When to Use

- When the user says "create a content brief", "give me a brief for this post", "plan this piece of content", or 「写一个内容简报」「给我这篇文章的 brief」/ 用户说「写一个内容简报」「给我这篇文章的 brief」「帮我规划这篇内容」时
- When upstream skills (content-gap, seo-audit) output keyword or gap opportunities / 当上游 skill（content-gap、seo-audit）输出关键词机会或 gap opportunity 时
- Before blog-post / linkedin-post starts, to pin down target, keywords, outline, and CTA / 在 blog-post / linkedin-post 开始前，需要明确 target、keywords、outline、CTA 时

## 前置上下文 / Required Context

Read these files BEFORE writing (per AGENTS.md, trust the docs over inference; do not re-infer): / 动笔前必须先读取以下文件（按 AGENTS.md，以文档为准、不重新推断）：

- `context/brand-voice.md` — required. Voice profile, word choice, no-go list. / 必读。语气画像、用词规范、禁用清单。
- `context/competitor-analysis.md` — required. Differentiation opportunities, competitor content & SEO comparison. / 必读。差异化机会、竞品内容与 SEO 对比。
- `context/content-strategy.md` — read to align with topic clusters, funnel stage, and content calendar. / 用于对齐主题集群、内容漏斗阶段与内容日历。
- `context/product-information.md` — read for value proposition, ICP, and keyword pool. / 用于引用价值主张、目标客户与关键词池。
- Need from user/upstream: topic/keyword, target audience, content goal (or a gap opportunity from content-gap). / 需要用户/上游提供：主题/关键词、目标受众、内容目标（或 content-gap 产出的 gap opportunity）。

## 输入 / Inputs

| 字段 | 必填 | 说明 |
|---|---|---|
| `topic_keyword` | ✅ | Topic / primary keyword, can come from the content-gap opportunity list. / 主题 / 主关键词，可来自 content-gap 的机会清单。 |
| `target_audience` | ✅ | Target audience / ICP, and which funnel stage they are in (TOFU/MOFU/BOFU). / 目标受众 / ICP，及其所处内容漏斗阶段（TOFU/MOFU/BOFU）。 |
| `content_goal` | ✅ | Content goal (awareness / acquisition / conversion / authority), or a gap opportunity from content-gap. / 内容目标（品牌认知 / 获客 / 转化 / 权威度），或 content-gap 产出的 gap opportunity。 |
| `secondary_keywords` | ❌ | Secondary / long-tail keywords; if missing, derive from the keyword pool in context/product-information.md and competitor comparison. / 次级关键词 / 长尾词；缺省时从 context/product-information.md 关键词池与竞品对比中推导。 |
| `internal_links` | ❌ | Internal pages to link to; if missing, derive from the topic clusters in context/content-strategy.md. / 可链接的站内内容；缺省时从 context/content-strategy.md 主题集群中推导。 |

## 输出 / Outputs

- Output file: `outputs/content-brief/<slug>.md` (slug = URL-ized primary keyword, e.g. `outputs/content-brief/how-to-choose-crm.md`). / 产出文件：`outputs/content-brief/<slug>.md`（slug 取主关键词的 URL 化形式）。
- Format: Markdown. / 格式：Markdown。
- Example structure: / 示例结构：

```markdown
# Content Brief: <Title>

## 基础信息 / Basics
- Slug / 目标关键词:
- 搜索意图 / Search Intent:
- 目标受众 / Audience:
- 漏斗阶段 / Funnel Stage:

## 关键词 / Keywords
- 主关键词 / Primary:
- 次级关键词 / Secondary:

## 大纲 / Outline
- H2: …
  - H3: …
  - H3: …

## 规格 / Specs
- 目标字数 / Word Count:
- CTA / Call to Action:
- 内链 / Internal Links:
- 语气参照 / Voice Ref: context/brand-voice.md
- 竞品参照 / Competitor Ref: context/competitor-analysis.md
```

## 验收项 / Acceptance Criteria

- [ ] Search intent is explicit (informational / navigational / transactional) / 明确写出搜索意图（信息型 / 导航型 / 交易型）
- [ ] Contains 1 primary keyword + ≥3 secondary keywords, consistent with search intent / 包含 1 个主关键词 + ≥3 个次级关键词，且与搜索意图一致
- [ ] Contains an H2/H3 outline covering every sub-question of the search intent / 包含 H2/H3 两级大纲，覆盖搜索意图的每个子问题
- [ ] States a target word count / 写明目标字数（Target Word Count）
- [ ] Contains a clear CTA matching the content goal and funnel stage / 包含明确的 CTA，与内容目标及漏斗阶段对应
- [ ] Lists internal links pointing to related topic-cluster pages / 列出内部链接（Internal Links，指向主题集群相关页）
- [ ] References `context/brand-voice.md` (voice, no-go list) and `context/competitor-analysis.md` (differentiation angle) / 引用 `context/brand-voice.md`（语气、禁用清单）与 `context/competitor-analysis.md`（差异化角度）
- [ ] Written to `outputs/content-brief/<slug>.md` for downstream consumption by blog-post / linkedin-post / 产出写入 `outputs/content-brief/<slug>.md`，供 blog-post / linkedin-post 下游消费

## 执行步骤 / Steps

1. Read the relevant `context/` docs (brand-voice, competitor-analysis, content-strategy, product-information). / 读取 `context/` 相关文档。
2. Confirm inputs: topic/keyword, audience, goal (if missing, ask the user or take the gap opportunity from content-gap output). / 确认输入：主题/关键词、受众、目标（若缺，询问用户或从 content-gap 输出中取 gap opportunity）。
3. Determine search intent and funnel stage (TOFU/MOFU/BOFU), then pick the CTA accordingly. / 判定搜索意图与漏斗阶段，据此确定 CTA。
4. Assemble primary + secondary keywords (prefer the product-information keyword pool and competitor comparison). / 组合主关键词 + 次级关键词（优先用 product-information 关键词池与竞品对比）。
5. Draft the H2/H3 outline covering the search intent; pick an angle from the competitor differentiation opportunities. / 起草 H2/H3 大纲，确保覆盖搜索意图；按竞品差异化机会找切入点。
6. Write the specs: word count, CTA, internal links; note the voice and competitor reference files. / 写规格：目标字数、CTA、内链；标明语气与竞品参照文件。
7. Write to `outputs/content-brief/<slug>.md` and self-check against the acceptance criteria. / 写入文件并自检验收清单。

## 脚本 / Scripts

No scripts — this is a pure writing/planning task. / 无脚本，纯写作/规划任务。

## 发布 / Publishing

This skill only produces an internal brief file with no external writes; the brief must be human-approved before being handed to blog-post / linkedin-post for execution. / 本 skill 只产出内部简报文件，无对外写操作；简报需人工确认后，方可交给 blog-post / linkedin-post 执行。
