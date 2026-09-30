---
name: website-research
description: When to use — fetch and analyze a website's structure, metadata, content, and sitemap to produce product and market intelligence. Use for "website research", "site analysis", "competitor website audit", "官网调研", "网站分析".
---

# website-research / 官网与网站调研

Fetches a target website, extracts its structure, metadata, content, and sitemap, and turns the raw data into product & market intelligence for the shared context layer. 抓取目标网站，提取结构、元数据、内容与 sitemap，转化为产品与市场情报写入共享上下文层。

## 用途 / Purpose

Fills `context/product-information.md` with real data scraped from the product's own website — the first step of the [研究] phase in the closed loop (see AGENTS.md §3). 从官网抓取真实信息填入 `context/product-information.md`，是闭环流水线中 [研究] 阶段的第一步（见 AGENTS.md 第 3 节）。

This skill answers: What is this product? How does it position itself? What pages, features, and keywords exist? 回答：这个产品是什么？它如何自我定位？有哪些页面、功能与关键词？

## 触发时机 / When to Use

- When the user asks to "research a website", "analyze this site", "what does this product do", or provides only a URL with no product context. 当用户要求「调研这个网站」「分析官网」「这个产品是做什么的」，或只给了一个 URL 而没有产品背景时。
- When `context/product-information.md` still contains （待填写） placeholders. 当 `context/product-information.md` 仍是「（待填写）」占位符时。
- As the first step before `competitor-analysis` or `content-gap`. 作为 `competitor-analysis` / `content-gap` 之前的第一步。

## 前置上下文 / Required Context

- Read `context/product-information.md` first — this skill both consumes and (after approval) updates it. 先读 `context/product-information.md`——本 skill 既消费它，也（经审批后）更新它。
- Read `context/competitor-analysis.md` and `context/content-strategy.md` if they exist, to frame positioning and keyword observations. 如存在，读 `context/competitor-analysis.md` 与 `context/content-strategy.md`，用于解读定位与关键词。
- Optionally read `context/brand-voice.md` to compare on-site tone against the declared brand voice. 可选读 `context/brand-voice.md`，对比官网语气与既定品牌语气。

## 输入 / Inputs

| 字段 | 必填 | 说明 |
|---|---|---|
| `website_url` | ✅ | Target URL to research, e.g. `https://example.com`. 要调研的网站 URL。 |
| `max_pages` | ❌ | Maximum pages to crawl (default 5). 最大抓取页数（默认 5）。 |
| `auth_token` | ❌ | Optional bearer token for private sites; injected via env var `SITE_FETCH_AUTH_TOKEN`, never hardcoded. 私有站点可选令牌；通过环境变量注入，绝不硬编码。 |

## 输出 / Outputs

- 产出文件：`outputs/website-research/site-profile.json` — raw machine-readable profile. 原始机器可读画像。
- 产出文件：updated `context/product-information.md` — filled with real findings (overwrite requires human approval, see 发布). 更新后的 `context/product-information.md`（覆盖前需人工审批，见「发布」）。
- 格式：JSON (site-profile.json) / Markdown (product-information.md)
- 示例结构 / Example structure:

```json
{
  "requested_url": "https://example.com",
  "domain": "example.com",
  "redirected": false,
  "robots_txt": {"found": true, "sitemaps": ["https://example.com/sitemap.xml"]},
  "sitemap": {"found": true, "url_count": 42, "urls": ["..."]},
  "pages": [{"url": "...", "title": "...", "meta_description": "...", "h1": [], "h2": [], "internal_links": [], "body_text": "..."}]
}
```

## 验收项 / Acceptance Criteria

- [ ] `site-profile.json` is valid JSON containing `title`, `meta` (description/OG tags), `headings` (H1/H2), and `links` (internal + external) for every crawled page. JSON 有效，且每个抓取页面含 title、meta（description/OG 标签）、headings（H1/H2）与 links（内链+外链）。
- [ ] Writes a **filled** `context/product-information.md` — no （待填写） placeholders left in the sections covered by findings. 写入了「已填写」的 `context/product-information.md`，相关小节不留「（待填写）」占位符。
- [ ] Handles redirects gracefully — records `final_url` and `redirected: true` instead of failing. 优雅处理重定向：记录 `final_url` 与 `redirected: true`，不报错。
- [ ] Handles a missing robots.txt / sitemap.xml gracefully — marks `found: false` with an error note, still returns homepage analysis. 优雅处理缺失的 robots.txt / sitemap.xml：标记 `found: false` 并附错误说明，仍返回首页分析。
- [ ] Script runs on Python 3.10+ stdlib only (urllib + html.parser), no third-party deps. 脚本仅用 Python 3.10+ 标准库（urllib + html.parser）运行，无第三方依赖。
- [ ] No secrets hardcoded; all credentials read from environment variables. 不硬编码任何凭据；一律从环境变量读取。
- [ ] Robots directives and sitemap URLs are captured for downstream SEO skills. robots 指令与 sitemap URL 已捕获，供下游 SEO skill 使用。

## 执行步骤 / Steps

1. Read the Required Context files listed above. 读取上方「前置上下文」所列文件。
2. Run the fetch script against the target URL. 对目标 URL 运行抓取脚本：

   ```bash
   python scripts/fetch_site.py --url https://example.com --max-pages 5
   ```

3. Save the JSON output to `outputs/website-research/site-profile.json`. 将 JSON 输出保存到 `outputs/website-research/site-profile.json`。
4. Analyze the profile: extract product name, positioning, key features (from H1/H2 + body text), pricing hints, target customers, and a keyword pool. 分析画像：提取产品名、定位、核心功能（H1/H2 + 正文）、定价线索、目标客户与关键词池。
5. Draft the updated `context/product-information.md` and request human approval before overwriting the shared doc. 起草更新后的 `context/product-information.md`，覆盖共享文档前请求人工审批。

## 脚本 / Scripts

```bash
python scripts/fetch_site.py --help
```

- `scripts/fetch_site.py` — fetches robots.txt + sitemap.xml, extracts title/meta description/OG tags/H1/H2/links/body text, prints JSON to stdout. 抓取 robots.txt + sitemap.xml，提取 title/meta description/OG 标签/H1/H2/链接/正文，输出 JSON 到 stdout。
- Flags: `--url` (required), `--max-pages` (default 5). 参数：`--url`（必填）、`--max-pages`（默认 5）。
- Stdlib only — no `requirements.txt` needed. 仅标准库——无需 `requirements.txt`。
- Env vars: `SITE_FETCH_USER_AGENT`, `SITE_FETCH_TIMEOUT`, `SITE_FETCH_AUTH_TOKEN`. 环境变量：`SITE_FETCH_USER_AGENT`、`SITE_FETCH_TIMEOUT`、`SITE_FETCH_AUTH_TOKEN`。

## 发布 / Publishing

Overwriting `context/product-information.md` is a shared-context write operation — requires two-phase human confirmation before the file is changed (see AGENTS.md §4). The `site-profile.json` under `outputs/` is written directly, no approval needed. 覆盖 `context/product-information.md` 属于共享上下文写操作——修改前需两阶段人工确认（见 AGENTS.md 第 4 节）。`outputs/` 下的 `site-profile.json` 可直接写入，无需审批。
