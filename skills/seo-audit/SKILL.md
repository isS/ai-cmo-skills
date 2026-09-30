---
name: seo-audit
description: When to use — perform a technical and on-page SEO audit of a website and return fixes ranked by impact. Use for "seo audit", "technical seo", "on-page seo", "website audit", or when asked to 做网站SEO审计 / 排查网站SEO问题.
---

# SEO Audit / SEO 审计

Runs a technical + on-page SEO audit of a website and produces a prioritized, actionable fix plan. / 对网站执行技术与页面级 SEO 审计，产出按影响排序、可直接执行的修复清单。

## 用途 / Purpose

- Diagnoses the crawlability and on-page SEO health of the site before any content production. / 在内容生产前诊断网站的可抓取性与页面级 SEO 健康度。
- Position in the closed loop: sits at the **[机会]** stage, feeding the `content-gap` skill with a clean technical baseline. / 闭环位置：位于 **[机会]** 阶段，为下游 `content-gap` 提供干净的技术底线。
- Output (`outputs/seo-audit/fix-plan.json`) is machine-readable so downstream skills/agents can consume it directly. / 产出为机器可读 JSON，供下游 skill 直接消费。

## 触发时机 / When to Use

- User says "audit my site's SEO", "SEO audit", "technical SEO check", "on-page SEO", "为什么我的页面搜不到/排名低". / 用户说「审计我网站的 SEO」「排查 SEO 问题」「网站为什么搜不到」时。
- When the upstream `website-research` skill has produced `context/product-information.md` and a site URL exists. / 上游 `website-research` 已产出产品信息且已有站点 URL 时。
- Before launching a content push: run this to make sure technical debt does not waste the new content. / 大规模内容投放前，先跑一次审计，避免技术债浪费新内容。

## 前置上下文 / Required Context

- MUST read `context/product-information.md` first — use its **Keyword Pool（关键词池）** to judge whether titles/descriptions target the right keywords. / 必须先读 `context/product-information.md`，用其关键词池判断标题/描述是否命中目标关键词。
- SHOULD read `context/competitor-analysis.md` — use its **Content & SEO（内容与 SEO 对比）** section to calibrate severity (e.g. a missing feature is only "high" if competitors have it). / 应读 `context/competitor-analysis.md`，用「内容与 SEO」对比校准问题严重度。
- Do NOT re-infer anything already documented in `context/`. If those files are empty/placeholder, note that in the fix plan instead of guessing. / `context/` 已有内容时以文档为准，不要重新推断；文档为空时在 fix 清单中注明，而非猜测。

## 输入 / Inputs

| 字段 | 必填 | 说明 |
|---|---|---|
| `url` | ✅ | The website URL to audit (any page; site-level checks run against its origin). / 待审计的网站 URL（任意页面均可，站点级检查基于其源站执行）。 |
| `crawl` | ❌ | Whether to crawl the sitemap and audit multiple pages (default: single page). / 是否爬取 sitemap 并审计多页（默认单页）。 |
| `sitemap_url` | ❌ | Explicit sitemap URL when it is not at the default `/sitemap.xml`. / 自定义 sitemap 地址（默认取 `/sitemap.xml`）。 |
| `max_pages` | ❌ | Cap on pages to audit when crawling (default 20). / 爬取模式下最多审计的页数（默认 20）。 |

## 输出 / Outputs

- 产出文件：`outputs/seo-audit/fix-plan.json`
- 格式：JSON（脚本直接打印到 stdout，可用 `--output` 同时落盘）
- 示例结构：

```json
{
  "generated_at": "2026-10-01T00:00:00Z",
  "audit": {"url": "https://example.com", "mode": "crawl", "pages_audited": 12},
  "fixes": [
    {"issue": "Missing <title> tag", "severity": "critical", "location": "https://example.com/pricing", "fix": "Add a unique 50-60 char <title> starting with the primary keyword."}
  ],
  "summary": {"critical": 1, "high": 2, "medium": 4, "low": 1, "total": 8}
}
```

- 排序规则：`critical > high > medium > low`，同级别保持稳定顺序（按影响从高到低）。/ Sorted high-to-low impact.

## 验收项 / Acceptance Criteria

- [ ] Every fix has a `severity` + a concrete `fix` action + a `location` (specific page URL or site-level element like `robots.txt`). / 每条修复都含严重度、具体动作、具体位置。
- [ ] Fixes are ranked high-to-low impact (`critical` → `high` → `medium` → `low`). / 按影响从高到低排序。
- [ ] No generic fluff — no "improve SEO" without a concrete, verifiable action. / 无空泛建议，每条可执行可验证。
- [ ] Each finding references a specific page/element (e.g. which page lacks an H1, which `<img>` lacks `alt`). / 每条发现指向具体页面或元素。
- [ ] Checks cover: title length, meta description, H1 uniqueness, image alt, canonical, schema.org markup, robots.txt/sitemap presence, internal linking. / 检查覆盖全部八项：标题长度、描述、H1 唯一性、图片 alt、canonical、结构化数据、robots/sitemap、内链。
- [ ] The JSON at `outputs/seo-audit/fix-plan.json` parses and can be consumed by the next skill (`content-gap`). / 产出 JSON 可解析、可被下游消费。

## 执行步骤 / Steps

1. Read `context/product-information.md` (keyword pool) and `context/competitor-analysis.md` (SEO comparison). / 读取两份前置上下文。
2. Run the audit script (single page or `--crawl` for a full pass). / 运行审计脚本（单页或 `--crawl` 全站）。
3. Review the ranked fixes; cross-check keyword alignment against the keyword pool; drop or downgrade anything already covered by competitor context. / 人工复核排序结果，与关键词池交叉比对，剔除与竞品上下文不符的项。
4. Save the JSON to `outputs/seo-audit/fix-plan.json`; write a one-paragraph triage summary for the next skill. / 保存 JSON，并写一段优先级摘要交给下游。
5. Hand the fix plan to `content-gap` so keyword opportunities build on a clean technical baseline. / 将 fix 清单交给 `content-gap`。

## 脚本 / Scripts

```bash
python scripts/seo_audit.py https://example.com            # audit one page
python scripts/seo_audit.py https://example.com --crawl    # crawl sitemap, audit up to 20 pages
python scripts/seo_audit.py --help                         # see all options
```

- 依赖：仅 Python 3.10+ 标准库，无 `requirements.txt`。/ stdlib only, no third-party deps.
- 凭据通过环境变量注入，绝不硬编码：`SEO_AUDIT_USER_AGENT`（可选 UA）、`SEO_AUDIT_BASIC_AUTH_USER` / `SEO_AUDIT_BASIC_AUTH_PASS`（可选 HTTP Basic 认证）、`SEO_AUDIT_TIMEOUT`（可选超时秒数）。/ Credentials via env vars only.

## 发布 / Publishing

- This skill performs **read-only** analysis of a public website; it writes only to local `outputs/seo-audit/`. No human approval gate required. / 本 skill 仅对公开站点做只读分析，只写本地 `outputs/`，无需人工审批。
- If audit findings lead to content changes, those changes flow through `content-brief` / `blog-post` and are published only by `cms-publish` after human approval. / 审计引发的任何内容改动必须经 `cms-publish` 人工审批后发布。
