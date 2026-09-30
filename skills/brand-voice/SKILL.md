---
name: brand-voice
description: When to use — extract and codify the brand's voice, tone, word choice rules and no-go list from positioning, ICP and sample copy, then write them to context/brand-voice.md. Use for "brand voice", "tone of voice", "voice profile", "copy style guide". 当你需要提炼并固化品牌语气、用词规范与禁用清单，供所有内容生产类 skill 统一引用时使用。
---

# Brand Voice / 品牌语气提炼

Extract the brand's voice from positioning, target audience and sample copy, and codify it into `context/brand-voice.md` so every content skill writes in one consistent voice. 从品牌定位、目标受众和样本文案中提炼品牌语气，固化为 `context/brand-voice.md`，让所有内容 skill 用同一套语气创作。

## 用途 / Purpose

In the closed loop, `brand-voice` sits between research (`website-research`, `competitor-analysis`) and content production (`content-brief`, `blog-post`, `linkedin-post`). It turns raw positioning and examples into a reusable, rule-based voice profile, preventing tone drift across channels. 在闭环中，本 skill 位于研究（website-research、competitor-analysis）与内容生产（content-brief、blog-post、linkedin-post）之间，把零散的定位与示例转化为可复用的规则化语气画像，防止跨渠道语气跑偏。

## 触发时机 / When to Use

- The user says "extract our brand voice", "define our tone of voice", "build a voice profile", or "write our copy style guide". 用户说「提炼品牌语气」「定义语气画像」「写一份文案风格指南」时。
- Upstream research skills have produced or updated `context/product-information.md` or `context/competitor-analysis.md`. 上游研究 skill 已产出或更新 `context/product-information.md`、`context/competitor-analysis.md` 时。
- Before any content production work starts, if `context/brand-voice.md` is missing or stale. 内容生产开始前，发现 `context/brand-voice.md` 缺失或过时时。

## 前置上下文 / Required Context

- Read `context/product-information.md` — for brand positioning and ICP. 读取 `context/product-information.md`，获取品牌定位与理想客户画像。
- Read `context/competitor-analysis.md` — to differentiate voice from competitors. 读取 `context/competitor-analysis.md`，避免语气与竞品趋同、找到差异化表达角度。
- Read `context/marketing-strategy.md` — to align voice with strategic direction and channel priorities. 读取 `context/marketing-strategy.md`，使语气与战略方向、渠道优先级一致。
- If `context/brand-voice.md` already exists, read it and update in place instead of rebuilding from scratch. 若 `context/brand-voice.md` 已存在，先读取并在原稿基础上更新，而非推翻重写。
- Requires from the user: brand positioning, target audience/ICP, and (optional) sample copy or URLs. 需要用户提供：品牌定位、目标受众/ICP，以及（可选）样本文案或链接。

## 输入 / Inputs

| 字段 | 必填 | 说明 |
|---|---|---|
| `brand_positioning` | ✅ | Brand name, one-line positioning, key value proposition. 品牌名、一句话定位、核心价值主张。 |
| `target_audience_icp` | ✅ | Ideal customer profile: industry, role, pain points, reading context. 理想客户画像：行业、角色、痛点、阅读场景。 |
| `sample_copy` | ❌ | Representative copy examples (landing page, blog, social, emails) or URLs to fetch. 代表性文案示例（落地页、博客、社媒、邮件）或其链接。 |

## 输出 / Outputs

- 产出文件：`context/brand-voice.md` — updated in place, preserving the existing section structure. 原位更新的 `context/brand-voice.md`，保留既有章节结构。
- 格式：Markdown
- 必备章节 / Required sections written into the file: Brand Positioning, Voice Profile, Word Choice, Examples, No-go List. 写入文档的必备章节：品牌定位、语气画像、用词规范、语气示例、禁用清单。

## 验收项 / Acceptance Criteria

- [ ] Covers brand positioning: brand name, one-line positioning, and target audience/ICP. 覆盖品牌定位：品牌名、一句话定位与目标受众/ICP。
- [ ] Voice profile filled in: formality, tone/attitude, jargon density, sentence length preference. 语气画像填写完整：正式程度、语气态度、行业术语密度、句式偏好。
- [ ] Word choice rules defined: ✅ preferred terms/signature expressions and ❌ avoided terms (clichés, hype words). 用词规范明确：✅ 推荐用词/标志性表达与 ❌ 禁用词（陈词滥调、夸大宣传词）。
- [ ] At least one before/after example pair showing the rewrite in the brand's voice. 至少一组改写前/改写后示例，展示品牌语气下的改写效果。
- [ ] No-go list populated: no overpromising, no competitor bashing, emoji policy, etc. 禁用清单已填写：不夸大承诺、不贬低竞品、emoji 使用规则等。
- [ ] Voice is consistent with `context/product-information.md` and differentiated from `context/competitor-analysis.md`. 语气与产品信息一致，且与竞品声音形成差异。
- [ ] No script required; no files outside `context/brand-voice.md` were modified. 本 skill 无需脚本；除 `context/brand-voice.md` 外未改动其他文件。

## 执行步骤 / Steps

1. Read `context/product-information.md`, `context/competitor-analysis.md`, `context/marketing-strategy.md`, and the existing `context/brand-voice.md` (if any). 读取产品信息、竞品分析、营销策略，以及既有的品牌语气文档（如有）。
2. Collect inputs from the user: brand positioning, target audience/ICP, and (optional) sample copy or URLs. 向用户收集输入：品牌定位、目标受众/ICP，以及（可选）样本文案或链接。
3. If URLs are provided, fetch the pages and extract representative copy samples. 若提供了链接，抓取页面并摘录代表性文案。
4. Draft the voice profile: decide formality, tone/attitude, jargon density, and sentence preference based on positioning, ICP and samples. 起草语气画像：依据定位、ICP 与示例确定正式程度、语气态度、术语密度与句式偏好。
5. Derive word choice rules: ✅ preferred terms and signature expressions from samples; ❌ avoided terms (clichés, hype, jargon overload). 提炼用词规范：从示例中归纳 ✅ 推荐用词与标志性表达；列出 ❌ 禁用词（陈词滥调、夸大、术语堆砌）。
6. Write before/after example pairs: take a generic or poorly-toned sentence, rewrite it in the brand's voice. 撰写改写前/后示例：取一句平庸或语气不符的句子，用品牌语气改写。
7. Fill the no-go list: no overpromising, no competitor bashing, emoji policy, and any brand-specific bans. 填写禁用清单：不夸大承诺、不贬低竞品、emoji 使用规则及品牌特有禁令。
8. Update `context/brand-voice.md` in place, preserving its existing section structure, and present the diff for approval. 原位更新 `context/brand-voice.md`，保留既有章节结构，并展示改动差异供审批。

## 脚本 / Scripts

None. This skill is fully prompt-driven; no scripts or dependencies. 无脚本。本 skill 完全由 prompt 驱动，无脚本与依赖。

## 发布 / Publishing

This skill overwrites `context/brand-voice.md`, a shared context document. Per AGENTS.md §4, overwriting any `context/` document is a write operation that requires two-phase human confirmation before the file is saved. 本 skill 会覆盖共享文档 `context/brand-voice.md`。根据 AGENTS.md 第 4 节，覆盖任何 `context/` 文档属于写操作，保存前必须经过两阶段人工确认。
