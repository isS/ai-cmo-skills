---
name: weekly-growth-report
description: When to use — pull GSC + GA4 data, attribute weekly growth, and produce a weekly report with next-week priorities. Use for "weekly report", "growth report", "weekly growth report", "traffic report", "GSC report", "GA4 report", or when asked to 生成周报 / 分析本周流量与增长 / 制定下周优先级.
---

# Weekly Growth Report / 周度增长报告

Pulls Search Console + Google Analytics data, attributes growth at page/keyword level, and produces a weekly report with a concrete next-week priority list. / 拉取 GSC + GA4 数据，按页面与关键词归因增长，产出周报并给出下周可执行的优先级清单。

## 用途 / Purpose

- Turns raw GSC/GA4 numbers into a growth narrative: what moved, why, and what to do next. / 把原始数据变成增长叙事：什么变了、为什么、下一步做什么。
- Position in the closed loop: sits at the **[度量]** stage — the last step of one iteration and the first input of the next. Its priority list feeds back into the **[机会]** stage (`content-gap` / `seo-audit`), closing the loop. / 闭环位置：位于 **[度量]** 阶段，是上一轮迭代的收尾、下一轮的开端；产出的优先级清单回流到 **[机会]** 阶段（`content-gap` / `seo-audit`），形成闭环。
- Output (`outputs/weekly-growth-report/weekly-report.md`) is human-readable for stakeholders; the JSON on stdout is machine-readable for the orchestrating Agent. / 产出 Markdown 供团队阅读，stdout 的 JSON 供编排 Agent 直接消费。

## 触发时机 / When to Use

- User says "weekly report", "growth report", "how did we do this week", "本周流量怎么样", "生成周报", "下周该做什么". / 用户说「周报」「本周增长如何」「生成周报」「下周优先级」时。
- At the end of a content iteration, after `content-brief` / `blog-post` / `cms-publish` have run, to measure their impact. / 一轮内容迭代结束后（发布动作完成后），度量其效果。
- When upstream `content-gap` has produced `outputs/content-gap/gap-opportunities.json` and/or `seo-audit` has produced `outputs/seo-audit/fix-plan.json` — the report should tie next-week priorities to those artifacts. / 上游 `content-gap` / `seo-audit` 已产出机会与 fix 清单时，报告须把下周优先级挂靠到这些产物上。

## 前置上下文 / Required Context

- MUST read `context/content-strategy.md` — use its **核心指标（KPI）** and **主题集群（Topic Clusters）** to judge whether this week's numbers hit the plan and to frame priorities around existing clusters. / 必须先读 `context/content-strategy.md`，用其 KPI 与主题集群判断本周是否达标、并把优先级挂到现有内容规划上。
- SHOULD read `context/competitor-analysis.md` — use its **内容与 SEO 对比（Content & SEO）** to interpret wins/losses (e.g. a traffic drop on a keyword a competitor recently targeted). / 应读 `context/competitor-analysis.md`，用「内容与 SEO」对比解释赢/输（例如某关键词被竞品近期主攻导致流量下滑）。
- MAY read `context/product-information.md` — use its **关键词池（Keyword Pool）** to filter priorities down to on-strategy terms. / 可读 `context/product-information.md`，用关键词池把优先级收敛到与产品相关的词上。
- Do NOT re-infer anything already documented in `context/`. If those files are empty/placeholder, note it in the report instead of guessing. / `context/` 已有内容时以文档为准，不要重新推断；文档为空时在报告中注明。

## 输入 / Inputs

| 字段 | 必填 | 说明 |
|---|---|---|
| `gsc_csv` | ✅（或 `--fetch gsc`） | GSC 导出 CSV（含 `query`、`page`、`clicks`、`impressions`、`ctr`、`position` 列；或 `--fetch gsc` 走 Search Console API） |
| `ga4_csv` | ✅（或 `--fetch ga4`） | GA4 导出 CSV（含页面路径、`sessions`、`users`、`conversions/key events` 列；或 `--fetch ga4` 走 GA4 Data API） |
| `start_date` / `end_date` | ✅ | 报告周期（ISO 格式 `YYYY-MM-DD`，通常为一周） |
| `prior_start` / `prior_end` | ❌ | 对比周期；缺省自动取同长度紧邻的前一周期 |
| `gsc_prior_csv` / `ga4_prior_csv` | ❌ | 对比周期数据 CSV（如不提供则复用本周文件，环比为 0） |
| `gap_file` | ❌ | `outputs/content-gap/gap-opportunities.json`，用于把下周优先级挂到内容缺口上 |
| `fix_file` | ❌ | `outputs/seo-audit/fix-plan.json`，用于把优先级挂到高影响 fix 上 |
| API 凭据（环境变量） | ❌ | 仅在 `--fetch` 模式需要：`GOOGLE_APPLICATION_CREDENTIALS`（或 `GSC_CREDENTIALS` / `GA4_CREDENTIALS` 指向服务账号 JSON）、`GA4_PROPERTY_ID`、`GSC_SITE` |

CSV 列名别名自动识别（大小写与常见导出表头兼容）：GSC 的 query 别名 `query`/`top queries`/`search query`，page 别名 `page`/`top pages`/`url`；GA4 的 page 别名 `page path and screen class`/`page path`，conversions 别名 `key events`/`conversions`/`purchases`。

## 输出 / Outputs

- 产出文件：`outputs/weekly-growth-report/weekly-report.md`
- 格式：Markdown（周报，双语标题）；脚本同时向 stdout 打印 JSON（可用 `--output-json` 另存文件）
- 示例结构（JSON）：

```json
{
  "skill": "weekly-growth-report",
  "period": {"start": "2026-09-22", "end": "2026-09-28"},
  "prior_period": {"start": "2026-09-15", "end": "2026-09-21"},
  "gsc": {
    "totals": {"clicks": 1420, "impressions": 89200, "ctr": 0.0159, "position": 18.4},
    "delta": {"clicks_pct": 12.3, "impressions_pct": 8.1},
    "top_pages": [{"page": "/blog/ai-cmo-tool", "clicks": 210, "impressions": 9400, "position": 6.2, "delta_clicks_pct": 24.0}],
    "top_queries": [{"query": "ai cmo tool", "clicks": 150, "impressions": 8200, "position": 5.1, "delta_clicks_pct": 30.0}],
    "wins": [{"target": "/blog/ai-cmo-tool", "delta_clicks": 40, "reason": "clicks up week-over-week"}],
    "losses": [{"target": "/pricing", "delta_clicks": -18, "reason": "clicks down week-over-week"}]
  },
  "ga4": {
    "totals": {"sessions": 2310, "users": 1870, "conversions": 96},
    "delta": {"sessions_pct": 9.4, "conversions_pct": 15.2},
    "top_pages": [{"page": "/", "sessions": 540, "conversions": 22}]
  },
  "priorities": [
    {"priority": 1, "action": "Publish pillar post targeting \"ai cmo tool\"", "target": "ai cmo tool", "rationale": "position 5.1 with 8200 impressions; content-gap estimated value 118.5", "source": "content-gap"}
  ]
}
```

- 优先级规则：CTR 机会（高展示低点击、排名 5–15）> 输项挽回（环比流失页面/关键词）> 内容缺口挂靠（`gap_file` 命中）> 高影响 fix 挂靠（`fix_file` 命中）。/ Priorities ranked: CTR opportunities > loss recovery > gap tie-ins > fix tie-ins.

## 验收项 / Acceptance Criteria

- [ ] Report includes traffic/click/impression trends for the period with week-over-week percentage deltas. / 报告包含流量/点击/展示趋势及环比变化百分比。
- [ ] Top pages and top keywords are listed with clicks/impressions/position. / 列出 Top 页面与 Top 关键词（含点击、展示、排名）。
- [ ] Wins and losses vs the prior period are explicitly identified and attributed to specific pages or keywords. / 明确标注相对上一周期的赢/输项，并归因到具体页面或关键词。
- [ ] A concrete next-week priority list exists, and each item is tied to a `content-gap` opportunity or an `seo-audit` fix wherever those artifacts are available. / 存在具体可执行的下周优先级清单，且每项尽可能挂靠 `content-gap` / `seo-audit` 产出。
- [ ] Script prints valid JSON to stdout and writes the Markdown report to `outputs/weekly-growth-report/weekly-report.md`. / 脚本向 stdout 输出合法 JSON，并写入 Markdown 周报。
- [ ] Secrets are read from environment variables only — no hardcoded credentials. / 凭据仅从环境变量读取，绝不硬编码。
- [ ] Script runs on Python 3.10+; CSV mode uses stdlib only (third-party deps only needed for `--fetch` API mode). / 脚本兼容 Python 3.10+；CSV 模式仅用标准库（第三方依赖仅 `--fetch` API 模式需要）。

## 执行步骤 / Steps

1. 读取前置上下文文档（`context/content-strategy.md` 必读，`context/competitor-analysis.md` 应读，可选 `context/product-information.md`）
2. 准备数据：从 GSC / GA4 导出 CSV，或配置凭据走 API（`GOOGLE_APPLICATION_CREDENTIALS`、`GA4_PROPERTY_ID`）
3. 运行脚本生成报告：

```bash
python skills/weekly-growth-report/scripts/gsc_ga4_report.py \
  --gsc-csv gsc-week.csv --ga4-csv ga4-week.csv \
  --start 2026-09-22 --end 2026-09-28 \
  --gap-file outputs/content-gap/gap-opportunities.json \
  --fix-file outputs/seo-audit/fix-plan.json
```

4. 人工/AI 复核：对照 `context/content-strategy.md` 的 KPI 判断达标情况，用 `context/competitor-analysis.md` 解释异常波动，剔除与产品无关的优先级项
5. 把周报写入 `outputs/weekly-growth-report/weekly-report.md`；把优先级清单回流给下游 `content-gap` / `seo-audit`，启动下一轮 [机会] 阶段

## 脚本 / Scripts

```bash
python scripts/gsc_ga4_report.py --help              # see all options
python scripts/gsc_ga4_report.py --fetch all \
  --site https://example.com/ --property 123456789 \
  --start 2026-09-22 --end 2026-09-28               # API mode (GSC + GA4)
```

- 依赖：CSV 模式仅 Python 3.10+ 标准库；`--fetch` API 模式需安装 `scripts/requirements.txt`（`google-api-python-client`、`google-auth`）
- 凭据通过环境变量注入，绝不硬编码：`GOOGLE_APPLICATION_CREDENTIALS`（服务账号 JSON 路径，GSC 与 GA4 共用；也可分别用 `GSC_CREDENTIALS` / `GA4_CREDENTIALS`）、`GA4_PROPERTY_ID`、`GSC_SITE`
- 输出：默认打印 JSON 到 stdout（Agent 可直接解析）；`--output` 写入 Markdown 周报，`--output-json` 可另存 JSON

## 发布 / Publishing

本 skill 为只读分析，无对外写操作，产物仅写入本地 `outputs/weekly-growth-report/`，无需人工审批。周报产出的下周优先级清单由下游 `content-gap` / `seo-audit` 消费后，才进入内容生产与 `cms-publish` 发布审批流程。
