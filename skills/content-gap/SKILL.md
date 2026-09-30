---
name: content-gap
description: "When to use — compare our keyword coverage against competitors to find content/keyword gaps and prioritize new content opportunities. Use for \"content gap\", \"keyword gap\", \"competitor keywords\", \"content opportunities\", \"gap analysis\". 用于发现我们与竞品之间的关键词与内容缺口。"
---

# Content Gap / 内容缺口分析

Finds keywords competitors target that we don't cover, ranks them by estimated value, and suggests a content angle for each gap. / 找出竞品覆盖而我们没有的关键词，按预估价值排序，并为每个缺口给出内容切入角度。

## 用途 / Purpose

Sits in the [机会] stage of the closed loop (after `seo-audit`, before `content-brief`). It turns raw keyword lists into a prioritized list of new-content opportunities, so the team writes content where competitors win and we don't yet compete. / 位于闭环的「机会」阶段（`seo-audit` 之后、`content-brief` 之前），把原始关键词清单转化为按优先级排序的新内容机会清单。

## 触发时机 / When to Use

- When the user says "content gap", "keyword gap", "what keywords are competitors ranking for that we aren't", "find content opportunities", "gap analysis" / 用户说「内容缺口」「关键词缺口」「找内容机会」「竞品关键词对比」时
- When upstream `seo-audit` or `competitor-analysis` has produced our/competitor keyword lists that need comparing / 上游 `seo-audit`、`competitor-analysis` 产出我方与竞品关键词清单后

## 前置上下文 / Required Context

- 先读取 `context/competitor-analysis.md` — who the competitors are, their main keywords, and differentiation opportunities / 竞品清单、竞品主攻关键词与差异化机会
- 先读取 `context/content-strategy.md` — topic clusters, funnel stages, and content calendar so gaps can be slotted into the existing plan / 主题集群、内容漏斗与内容日历，便于把缺口并入现有计划
- 可选读取 `context/product-information.md` — 关键词池（Keyword Pool）用于过滤与产品无关的机会
- 需要用户提供：我方关键词列表与一个或多个竞品关键词列表（JSON），或 GSC 导出（CSV）

## 输入 / Inputs

| 字段 | 必填 | 说明 |
|---|---|---|
| `our_file` | ✅ | 我方关键词 JSON 文件路径，或 GSC 导出 CSV |
| `competitor_files` | ✅ | 一个或多个竞品关键词 JSON 文件路径（可多个） |

JSON 文件格式（我方）：

```json
{
  "site": "example.com",
  "keywords": [
    { "keyword": "ai marketing platform", "volume": 320, "difficulty": 28 }
  ]
}
```

JSON 文件格式（竞品）：

```json
{
  "competitor": "competitor-a.com",
  "keywords": [
    { "keyword": "ai cmo tool", "volume": 150, "difficulty": 21, "clicks": 12, "impressions": 900 }
  ]
}
```

GSC 导出 CSV 至少包含 `query` 列；可选 `clicks`、`impressions`、`position` 列（脚本自动识别）。关键字字段别名兼容 `keyword` / `query` / `term`，搜索量别名兼容 `volume` / `search_volume` / `vol`，难度别名兼容 `difficulty` / `kd` / `difficulty_score`。

## 输出 / Outputs

- 产出文件：`outputs/content-gap/gap-opportunities.json`
- 格式：JSON（同时打印到 stdout）
- 示例结构：

```json
{
  "skill": "content-gap",
  "our_source": "example.com",
  "our_keywords_analyzed": 120,
  "competitor_files": [{ "file": "competitor-a.json", "source": "competitor-a.com" }],
  "gap_count": 3,
  "gaps": [
    {
      "keyword": "ai cmo tool",
      "volume": 150,
      "difficulty": 21,
      "estimated_value": 118.5,
      "sources": ["competitor-a.com"],
      "suggested_angle": "Pillar blog post targeting \"ai cmo tool\" (est. volume 150)"
    }
  ]
}
```

## 验收项 / Acceptance Criteria

- [ ] Gap keywords are flagged with source and a suggested content angle each / 每个缺口关键词都标注了来源与建议内容角度
- [ ] Results sorted by priority (estimated value, descending) / 结果按优先级（预估价值）降序排序
- [ ] No false positives on already-covered terms (normalized exact match, deduped) / 已覆盖词无漏网误报（归一化精确匹配 + 去重）
- [ ] Script runs on Python 3.10+ with stdlib only; prints valid JSON to stdout / 脚本仅用标准库，可在 Python 3.10+ 运行并向 stdout 输出合法 JSON
- [ ] Secrets read from environment variables only (none required for local comparison) / 凭据仅从环境变量读取（本地比较无需凭据）

## 执行步骤 / Steps

1. 读取前置上下文文档（`context/competitor-analysis.md`、`context/content-strategy.md`，可选 `context/product-information.md`）
2. 准备输入文件：我方关键词 JSON 与竞品关键词 JSON（或 GSC 导出 CSV）
3. 运行脚本比较并生成结果：

```bash
python skills/content-gap/scripts/keyword_gap.py OUR.json COMP1.json COMP2.json \
  --output outputs/content-gap/gap-opportunities.json
```

4. 人工/AI 复核结果：剔除与产品无关的关键词，确认每个 suggested angle 符合品牌语气与内容策略
5. 把最终机会清单写入 `outputs/content-gap/gap-opportunities.json`，交给下游 `content-brief` 消费

## 脚本 / Scripts

```bash
python skills/content-gap/scripts/keyword_gap.py --help
```

- 依赖：Python 3.10+ 标准库，无第三方依赖（无需 `requirements.txt`）
- 凭据：本脚本为纯本地文件比较，无外部 API；若将来接入关键词 API，凭据必须通过环境变量注入（如 `KEYWORD_API_TOKEN`），绝不硬编码
- 输出：默认打印 JSON 到 stdout（Agent 可直接解析）；`--output` 可同时写入文件

## 发布 / Publishing

本 skill 为只读分析，无对外写操作，产物仅写入本地 `outputs/content-gap/`，无需人工审批。机会清单由下游 `content-brief` 消费后才进入内容生产与发布审批流程。
