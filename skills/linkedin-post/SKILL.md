---
name: linkedin-post
description: When to use — write LinkedIn posts (single or series) from source content, optimized for reach and engagement. Use for "linkedin post", "linkedin content", "social post", "thought leadership". 中文触发词：领英帖子、领英内容、社媒文案。
---

# LinkedIn Post / 领英帖子

Turn source content (blogs, briefs, insights) into LinkedIn posts — single or series — optimized for reach and engagement.
将源内容（博客、简报、洞察）改写为领英帖子（单条或系列），优化传播与互动。

## Purpose / 用途

This skill sits in the [生产] production stage of the closed loop: it consumes `content-brief` / `blog-post` outputs and produces platform-ready LinkedIn drafts stored in `outputs/linkedin-post/` for downstream review and manual publishing.

- 解决什么问题：把长内容改写成适合 LinkedIn 信息流的短内容，提升触达与互动。
- 在闭环中的位置：生产阶段 → 产出待审稿件到 outputs/ → 人工审批后对外发布。

## When to Use / 触发时机

Use this skill when:

- The user asks for a "linkedin post", "linkedin content", "social post", or "thought leadership" piece（用户说「写一篇领英帖子 / 领英内容 / 社媒文案」时）
- An upstream skill (`content-brief` / `blog-post`) has produced content ready to repurpose for social（上游 skill 输出博客或简报、需要复用到社媒时）

## Required Context / 前置上下文

Read the following context files first（按需读取，优先以文档为准，不要重新推断）:

- `context/brand-voice.md` — REQUIRED. Voice profile and no-go list; all content-production skills must read it before writing.
- `context/product-information.md` — REQUIRED. Product facts, value proposition, and target customers to ground the post.
- `context/competitor-analysis.md` — OPTIONAL. Read only when the post needs differentiation angles vs. competitors.

Also require from the user（需要用户提供）:

- Source content/brief（待改写的源内容/简报）
- Campaign goal: `awareness` / `engagement` / `lead_gen`（目标：品牌认知/互动/获客）
- Whether to write a single post or a series（单条还是系列）

## Inputs / 输入

| Field | Required | Description |
|---|---|---|
| `source_content` | ✅ | Source material to repurpose: blog draft, content brief, product note, or key insights（源内容/简报） |
| `goal` | ✅ | Campaign objective: `awareness` / `engagement` / `lead_gen`（目标：品牌认知 / 互动 / 获客） |
| `brand_voice` | ✅ | Point to `context/brand-voice.md`; never invent the voice（品牌语气，以 brand-voice.md 为准） |
| `slug` | ✅ | Output file slug, e.g. `how-we-cut-onboarding-time`（输出文件名） |
| `series` | ❌ | If provided, write a multi-post series (N posts) instead of a single post（是否系列帖，含条数） |

## Outputs / 输出

- 产出文件 / Output file: `outputs/linkedin-post/<slug>.md`
- 格式 / Format: Markdown
- 示例结构 / Example structure:

```
# <Post title / 帖子标题>

## Main post / 主帖
- Hook (line 1-2)
- 3-5 short paragraphs
- CTA
- Hashtags (3-5)

## Variant A / 变体 A
（alternative hook or angle / 不同钩子或角度）

## Variant B / 变体 B
（alternative hook or angle / 不同钩子或角度）

## Series (optional) / 系列帖（可选）
- Post 1..N with a narrative arc（一条帖子一个观点）
```

## Acceptance Criteria / 验收项

- [ ] Hook appears within the first 2 lines（前 2 行内出现钩子）
- [ ] Short, scannable paragraphs — 1-3 lines each, no walls of text（段落短小、易扫读）
- [ ] Clear CTA at the end of each post（每条帖子结尾有明确 CTA）
- [ ] Includes 2+ variants (alternative hooks or angles)（包含 2 个及以上变体）
- [ ] Hashtags limited to 3-5 per post — no hashtag stuffing（每帖 3-5 个话题标签，不堆砌）
- [ ] Respects the brand voice no-go list from `context/brand-voice.md`（遵守 brand-voice.md 禁用清单）

## Steps / 执行步骤

1. Read `context/brand-voice.md` and `context/product-information.md`（读取品牌语气与产品信息文档）.
2. Confirm the goal (`awareness` / `engagement` / `lead_gen`) and whether a series is needed（确认目标与是否系列帖）.
3. Extract the strongest insight or value point from the source content as the hook（从源内容提炼最有价值的洞察作为钩子）.
4. Draft the main post: hook (lines 1-2) → 3-5 short paragraphs → CTA → 3-5 hashtags（撰写主帖）.
5. Write 2+ variants with different hooks or angles（撰写 2 个以上变体）.
6. If a series is requested, plan the narrative arc across posts — one idea per post（如为系列帖，规划叙事弧线，每条一个观点）.
7. Run the acceptance checklist and fix any failing items（对照验收项自查并修正）.
8. Write the draft to `outputs/linkedin-post/<slug>.md` and report the file path for review（写入产出文件并报告路径待审）.

## Publishing / 发布

This skill only produces drafts — it performs no external write operations（本 skill 仅产出草稿，不执行对外写操作）.

- Outputs go to `outputs/linkedin-post/<slug>.md` and must be reviewed by a human（产出待人工审阅）.
- Actual posting to LinkedIn is a write operation handled downstream; per AGENTS.md §4, sending any external message requires two-stage human confirmation（对外发布领英帖子属写操作，需两阶段人工确认）.
