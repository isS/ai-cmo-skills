---
name: competitor-analysis
description: When to use — analyze competitor positioning, content, and SEO to produce a comparison matrix plus differentiation opportunities. Use for "competitor analysis", "competitive research", "competitor comparison", "market positioning". 用于竞品分析、竞品调研、竞品对比与差异化机会挖掘。
---

# Competitor Analysis / 竞品分析

Fetches competitor websites and produces a positioning/content/SEO comparison matrix with concrete differentiation opportunities and threats. 抓取并分析竞品网站，产出定位、内容与 SEO 对比矩阵，并给出具体的差异化机会与威胁。

## 用途 / Purpose

Sits in the [研究] phase of the closed loop, right after `website-research` (see AGENTS.md §3). Its matrix and opportunity list feed `content-gap`, `content-brief`, `blog-post`, and `seo-audit` decisions. 位于闭环流水线的 [研究] 阶段，承接 `website-research`（见 AGENTS.md 第 3 节）；产出的对比矩阵与机会清单供 `content-gap`、`content-brief`、`blog-post`、`seo-audit` 决策使用。

This skill answers: What are competitors doing? Where do we stand? Where can we attack? 回答：竞品在做什么？我们差在哪？能从哪里进攻？

## 触发时机 / When to Use

- When the user says "analyze competitors", "competitive research", "competitor comparison", or 「分析竞品」「竞品对比」「竞争对手调研」. 当用户说「分析竞品」「竞品对比」「竞争对手调研」「competitor analysis」时。
- When `website-research` has produced product/category context and the market landscape is needed. 当上游 `website-research` 已输出官网与品类信息、需要摸清市场格局时。
- When looking for differentiation keywords/topics for the content strategy. 当需要为内容策略寻找差异化关键词 / 话题机会时。

## 前置上下文 / Required Context

- Read `context/product-information.md` first — our positioning, features, and keyword pool are the comparison baseline. 先读取 `context/product-information.md`：了解自家定位、功能与关键词池，作为对比基准。
- Read `context/brand-voice.md` — brand positioning and ICP determine audience overlap with each competitor. 先读取 `context/brand-voice.md`：了解品牌定位与 ICP，判断与竞品的受众重叠度。
- Read `context/competitor-analysis.md` — build incrementally on existing competitor data instead of rewriting from scratch. 先读取 `context/competitor-analysis.md`：基于既有竞品数据做增量更新，不凭空重写。
- Requires the user to provide: a competitor URL list (JSON file or a single URL). 需要用户提供：竞品 URL 列表（JSON 文件或单个 URL）。

## 输入 / Inputs

| 字段 | 必填 | 说明 |
|---|---|---|
| `competitors` | ✅ | A JSON array of competitor website URLs, e.g. `["https://a.com", "https://b.com"]`; a single URL string is also accepted. JSON 数组的竞品官网 URL（如 `["https://a.com","https://b.com"]`），也支持单个 URL 字符串。 |
| `input.json` | ✅ | Path to the input file passed to the script, shaped as above. 传给脚本的输入文件路径，结构见上。 |
| `COMPETITOR_USER_AGENT` | ❌ | Env var: custom User-Agent header (some sites block default agents). 环境变量：自定义请求 User-Agent（部分站点反爬需要）。 |
| `COMPETITOR_FETCH_TIMEOUT` | ❌ | Env var: per-request timeout in seconds, default 15. 环境变量：单请求超时秒数，默认 15。 |

## 输出 / Outputs

- 产出文件：`outputs/competitor-analysis/competitor-matrix.json` — machine-readable matrix. 机器可读对比矩阵。
- 同步更新：updated `context/competitor-analysis.md` — overwrite of a shared doc, requires human approval (see Publishing). 更新后的 `context/competitor-analysis.md`（覆盖共享文档，须人工审批，见「发布」）。
- 格式：JSON (competitor-matrix.json) / Markdown (competitor-analysis.md)
- 示例结构 / Example structure:

```json
{
  "generated_at": "2026-10-01T00:00:00+00:00",
  "competitors": [
    {
      "url": "https://competitor-a.com",
      "status": "ok",
      "title": "...",
      "meta_description": "...",
      "headings": {"h1": [], "h2": [], "h3": []},
      "keyword_hints": [{"keyword": "...", "count": 3}]
    }
  ],
  "matrix": {
    "dimensions": ["positioning", "pricing", "audience", "strengths", "weaknesses"],
    "rows": [
      {"competitor": "...", "positioning": "...", "pricing": "...", "audience": "...", "strengths": "...", "weaknesses": "..."}
    ]
  },
  "differentiation_opportunities": ["..."],
  "threats": ["..."]
}
```

## 验收项 / Acceptance Criteria

- [ ] Matrix covers positioning/pricing/audience/strengths/weaknesses. 矩阵覆盖定位、定价、受众、优势、劣势五个维度。
- [ ] Lists concrete differentiation opportunities and threats (specific, not generic). 列出具体的差异化机会与威胁（非泛泛而谈）。
- [ ] `outputs/competitor-analysis/competitor-matrix.json` is written and is valid JSON. `outputs/competitor-analysis/competitor-matrix.json` 已生成且为合法 JSON。
- [ ] `context/competitor-analysis.md` is updated: competitor list, positioning matrix, content & SEO comparison. `context/competitor-analysis.md` 已更新：竞品清单、定位矩阵、内容与 SEO 对比。
- [ ] Conclusions are grounded in real fetch data (title/meta/headings/keyword_hints) from `fetch_competitors.py`, not guessed. 结论基于 `fetch_competitors.py` 的实际抓取数据（title/meta/headings/keyword_hints），非凭空推断。
- [ ] Two-phase human confirmation completed before overwriting the shared `context/` doc. 覆盖 `context/` 共享文档前已完成两阶段人工确认。

## 执行步骤 / Steps

1. Read the Required Context files listed above. 读取上方「前置上下文」所列文件。
2. Run the fetch script against the competitor URLs. 运行脚本抓取竞品页面：

   ```bash
   python skills/competitor-analysis/scripts/fetch_competitors.py competitors.json
   ```

3. For each competitor, derive positioning, pricing, audience, strengths, and weaknesses from the fetched title / meta / headings / keyword_hints. 基于抓取到的 title / meta / headings / keyword_hints，逐竞品归纳定位、定价、受众、优势、劣势。
4. Compare against our product (`product-information.md`) and brand ICP (`brand-voice.md`) to build the differentiation opportunity list and threat list. 对照自家产品（product-information.md）与品牌 ICP（brand-voice.md），产出差异化机会清单与威胁清单。
5. Write the matrix to `outputs/competitor-analysis/competitor-matrix.json`. 将矩阵写入 `outputs/competitor-analysis/competitor-matrix.json`。
6. Show the user an update draft, and only after two-phase confirmation overwrite `context/competitor-analysis.md`. 向用户展示更新草案，经两阶段确认后覆盖 `context/competitor-analysis.md`。

## 脚本 / Scripts

```bash
python skills/competitor-analysis/scripts/fetch_competitors.py --help
python skills/competitor-analysis/scripts/fetch_competitors.py competitors.json
```

- `scripts/fetch_competitors.py` — fetches each URL, extracts title/meta description/keywords/OG tags and h1/h2/h3 headings, derives keyword hints, and prints a comparison JSON document to stdout. 抓取每个 URL，提取 title/meta description/keywords/OG 标签与 h1/h2/h3 标题，提取关键词线索，输出对比 JSON 到 stdout。
- Args: `input` (required JSON file), `-o/--output` (optional file to also write the result). 参数：`input`（必填 JSON 文件）、`-o/--output`（可选，同时把结果写入文件）。
- Stdlib only (Python 3.10+, urllib + html.parser) — no `requirements.txt` needed. 仅标准库（Python 3.10+，urllib + html.parser）——无需 `requirements.txt`。
- Secrets/config read from environment variables only, never hardcoded: `COMPETITOR_USER_AGENT`, `COMPETITOR_FETCH_TIMEOUT`; `HTTP_PROXY`/`HTTPS_PROXY` are honored automatically by urllib. 凭据一律从环境变量读取，绝不硬编码：`COMPETITOR_USER_AGENT`、`COMPETITOR_FETCH_TIMEOUT`；urllib 自动遵循 `HTTP_PROXY`/`HTTPS_PROXY`。

## 发布 / Publishing

Overwriting `context/competitor-analysis.md` is a shared-context write operation — requires two-phase human confirmation before the file is changed (see AGENTS.md §4): first present the draft, then confirm the overwrite. `outputs/` files are written directly, no approval needed. No outbound publishing. 覆盖 `context/competitor-analysis.md` 属于共享上下文写操作——修改前须两阶段人工确认（见 AGENTS.md 第 4 节）：先展示草案、再确认覆盖；`outputs/` 下的文件可直接写入，无需审批；本 skill 无对外发布动作。
