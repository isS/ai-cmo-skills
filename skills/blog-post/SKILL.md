---
name: blog-post
description: When to use — write a publishable long-form blog post from a content brief, in brand voice. Use for "blog post", "write article", "long-form content", "blog draft". 把内容简报写成可发布的博客长文。
---

# blog-post / 博客文章

Write a publishable long-form blog post from a content brief, in brand voice. / 根据内容简报，用品牌语气写一篇可发布的长篇博客文章。

## 用途 / Purpose

This skill turns a structured content brief (from `content-brief`) into a finished, publishable blog draft. It sits in the production stage of the closed loop: `content-brief → blog-post → cms-publish`. The output is a draft that awaits human review before publishing — it never publishes directly. / 本 skill 把 `content-brief` 产出的内容简报转化为一篇完成度可发布的博客草稿，位于闭环的「生产」环节：`content-brief → blog-post → cms-publish`。产出为待人工审核的草稿，绝不直接发布。

## 触发时机 / When to Use

- When the user says 「写一篇博客」「根据这个 brief 写文章」「blog post」「write article」「long-form content」/ 用户说「写一篇博客」「根据这个 brief 写文章」等时
- When the upstream `content-brief` skill has produced `outputs/content-brief/<slug>.md` / 当上游 `content-brief` skill 产出 `outputs/content-brief/<slug>.md` 时
- When repurposing a `linkedin-post` or refreshing old content into a long-form article / 当需要把短内容扩写或刷新为长文时

## 前置上下文 / Required Context

Read these files BEFORE writing (per AGENTS.md, trust the docs over inference; do not re-infer): / 动笔前必须先读取以下文件（按 AGENTS.md，以文档为准、不重新推断）：

- `context/brand-voice.md` — required. Voice profile, word choice, no-go list. Every sentence must respect it. / 必读。语气画像、用词规范、禁用清单，每句话都要遵守。
- `context/product-information.md` — required. Facts, features, value props used in the body and CTA. / 必读。正文与 CTA 引用的产品事实、功能、价值主张。
- `context/competitor-analysis.md` — read to differentiate angles and avoid claims competitors already own. / 用于寻找差异化角度、避开竞品已占据的论点。
- `context/content-strategy.md` — read to align with topic clusters, funnel stage, and target keywords. / 用于对齐主题集群、内容漏斗阶段与目标关键词。
- The content brief itself: `outputs/content-brief/<slug>.md` (or the topic + keywords provided by the user). / 内容简报本身：`outputs/content-brief/<slug>.md`（或用户直接提供的主题 + 关键词）。

## 输入 / Inputs

| 字段 | 必填 | 说明 |
|---|---|---|
| `brief` | ✅ | A content brief file (`outputs/content-brief/<slug>.md`) containing search intent, primary + secondary keywords, H2/H3 outline, target word count, CTA, and internal links. / 内容简报文件，含搜索意图、主/次关键词、H2/H3 大纲、目标字数、CTA 与内链。 |
| `topic` + `keywords` | ✅ | If no brief file exists, the user must supply at least a topic and primary keywords. / 若没有简报文件，用户至少提供主题与主关键词。 |
| `brand_voice` | ✅ | `context/brand-voice.md` — must be read, not assumed. / 必读 `context/brand-voice.md`，不允许凭空假设。 |

## 输出 / Outputs

- Output file: `outputs/blog-post/<slug>.md` — a complete, publishable Markdown draft. / 产出文件：`outputs/blog-post/<slug>.md` —— 一篇完整的、可发布的 Markdown 草稿。
- Format: Markdown with valid frontmatter (`title`, `slug`, `description`/meta description, `keywords`, `word_count`). / 格式：带合法 frontmatter 的 Markdown。
- Example structure: / 示例结构：

```markdown
---
title: <SEO title, keyword in front>
slug: <slug>
description: <150-char meta description with keyword>
keywords: [primary, secondary, ...]
word_count: <actual count>
---

# <H1, mirrors title>

<Hook intro: 3-5 sentences that open a loop>

## <H2 following the brief outline>
...

### <H3 as needed>

## <H2 ...>
...

## Conclusion / 结论
<Summary + CTA>
```

## 验收项 / Acceptance Criteria

- [ ] Matches the brief (topic, outline, keywords, intent) and the brand voice in `context/brand-voice.md` / 内容与简报（主题、大纲、关键词、意图）及品牌语气一致
- [ ] SEO-optimized: keyword in title, H1, meta description, and naturally placed in body (no stuffing) / SEO 达标：关键词出现在标题、H1、meta description 中，正文自然分布（不堆砌）
- [ ] Has a hook intro, structured H2/H3 body, conclusion, and a clear CTA / 具备钩子式开头、结构化正文、结论与明确 CTA
- [ ] Human-quality writing: specific claims, concrete examples, no AI filler ("in today's fast-paced world", "delve", empty transitions) / 内容如真人撰写：具体论点与实例，无 AI 套话与空泛过渡
- [ ] Correct Markdown: valid frontmatter, consistent heading levels, proper lists/links, renders cleanly / Markdown 规范：frontmatter 合法、标题层级一致、列表与链接正确、渲染正常
- [ ] Respects the no-go list: no exaggeration, no competitor bashing, no emoji (unless brand explicitly allows) / 遵守禁用清单：不夸大、不贬低竞品、不使用 emoji（除非品牌明确允许）
- [ ] Written to `outputs/blog-post/<slug>.md` / 已写入 `outputs/blog-post/<slug>.md`

## 执行步骤 / Steps

1. Read the content brief (or collect topic + keywords from the user). / 读取内容简报（或向用户收集主题与关键词）。
2. Read `context/brand-voice.md`, `context/product-information.md`, `context/competitor-analysis.md`, `context/content-strategy.md`. / 读取上述 context 文档。
3. Draft the frontmatter: title (keyword first), slug, meta description ≤ 150 chars, keywords, target word count. / 起草 frontmatter。
4. Write the hook intro that states the problem or stakes and opens a loop. / 写钩子式开头。
5. Write the body following the brief's H2/H3 outline; place keywords naturally; cite product facts and differentiation angles from context. / 按大纲写正文，关键词自然分布，引用 context 中的产品事实与差异化角度。
6. Write the conclusion summarizing the takeaway, then a single clear CTA (trial, demo, next article, etc.). / 写结论与单一明确 CTA。
7. Self-review against every Acceptance Criteria item; rewrite any AI-filler sentences. / 对照验收项自查，删除或改写所有 AI 套话。
8. Save to `outputs/blog-post/<slug>.md` and report the file path + word count. / 保存文件并汇报路径与字数。

## 发布 / Publishing

This skill only writes a draft — it never publishes. Publishing requires `cms-publish` after a two-phase human confirmation (per AGENTS.md §4). The agent must explicitly ask the user to review the draft before any publish step. / 本 skill 只产出草稿，不发布。发布必须经 `cms-publish` 且经过两阶段人工确认（AGENTS.md §4）。在执行任何发布动作前，Agent 必须请用户先审阅草稿。
