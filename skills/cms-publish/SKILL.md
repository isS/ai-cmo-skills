---
name: cms-publish
description: When to use — publish (or save as draft) a reviewed content file to a CMS via its REST API (WordPress/Webflow/custom) after a two-phase human approval gate. Use for "publish content", "publish to CMS", "cms publish", "push live", "create draft". 经人工审批后把内容发布到 CMS。
---

# cms-publish / CMS 发布

Publish reviewed content to WordPress / Webflow / a custom CMS via its REST API, with a mandatory two-phase human approval gate. / 通过 REST API 把审核通过的内容发布到 WordPress / Webflow / 自定义 CMS，并强制两阶段人工审批。

## 用途 / Purpose

This is the final publish stage of the closed loop (`blog-post / linkedin-post → cms-publish`). It takes an approved draft file and POSTs it to a CMS as either a draft or a live publish. It never bypasses human approval: live publishing requires two-phase confirmation (AGENTS.md §4), and the script defaults to draft mode. / 这是闭环的「发布」环节（`blog-post / linkedin-post → cms-publish`）。它把审核通过的草稿文件 POST 到 CMS，可选择存为草稿或正式发布。绝不绕过人工审批：正式发布必须两阶段确认（AGENTS.md §4），且脚本默认只存草稿。

## 触发时机 / When to Use

- When the user says 「发布这篇文章」「把这个发到 CMS」「publish this post」「push live」「cms publish」/ 用户说「发布这篇文章」「把这个发到 CMS」等时
- When an upstream skill (`blog-post`, `linkedin-post`) has produced `outputs/<skill>/<slug>.md` and the user has reviewed and approved it / 当上游 skill（`blog-post`、`linkedin-post`）产出草稿且用户已审阅通过时
- When updating or republishing existing content / 当需要更新或重新发布已有内容时

## 前置上下文 / Required Context

Read these BEFORE publishing (per AGENTS.md, trust the docs over inference; do not re-infer): / 发布前先读取以下文件（按 AGENTS.md，以文档为准、不重新推断）：

- The content file itself: `outputs/blog-post/<slug>.md` (or `.html`) — the payload to publish. / 内容文件本身：`outputs/blog-post/<slug>.md`（或 `.html`）—— 待发布的载荷。
- `context/brand-voice.md` — final compliance check against the no-go list (no exaggeration, no emoji, no competitor bashing) before anything goes live. / 上线前最后对照禁用清单（不夸大、不用 emoji、不贬低竞品）做合规检查。
- `context/content-strategy.md` — verify the piece matches the topic cluster, funnel stage, and channel plan before publishing. / 确认内容与主题集群、漏斗阶段、渠道计划一致再发布。
- `context/competitor-analysis.md` — cross-check any competitive or differentiation claims in the piece against the documented positioning matrix before they go live. / 上线前核对文中竞争性与差异化表述是否与文档中的定位矩阵一致。
- Env secrets: `CMS_TYPE`, `CMS_API_URL`, `CMS_API_TOKEN` — provided by the user/operator via environment variables, never hardcoded. / 环境变量凭据：`CMS_TYPE`、`CMS_API_URL`、`CMS_API_TOKEN` —— 由用户/运维通过环境变量提供，绝不硬编码。

## 输入 / Inputs

| 字段 | 必填 | 说明 |
|---|---|---|
| `content_file` | ✅ | Path to a Markdown or HTML content file (e.g. `outputs/blog-post/<slug>.md`). / 待发布的 Markdown 或 HTML 内容文件路径。 |
| `target_cms` | ✅ | Which CMS to hit, via the `CMS_TYPE` env var: `wordpress` \| `webflow` \| `custom`. / 目标 CMS，通过 `CMS_TYPE` 环境变量指定：`wordpress` \| `webflow` \| `custom`。 |
| `publish_or_draft` | ✅ | Explicit decision per run: `--draft` (default, safe) or `--publish` (only after two-phase human approval). / 每次运行的明确决定：`--draft`（默认，安全）或 `--publish`（仅在两阶段人工审批之后）。 |
| `title` / `slug` | ❌ | Optional overrides; otherwise inferred from the file's frontmatter, first H1, or filename. / 可选覆盖项；缺省时从文件 frontmatter、首个 H1 或文件名推断。 |

## 输出 / Outputs

- Primary output: a single JSON object printed to **stdout** — machine-parseable by the orchestrating agent. / 主要产出：一行 JSON 打印到 **stdout**，供编排 Agent 直接解析。
- Format: JSON. / 格式：JSON。
- Example (draft): `{"ok": true, "cms_type": "wordpress", "status": "draft", "http_status": 201, "post_id": 123, "url": "https://example.com/?p=123"}` / 示例（存草稿）
- Example (published): `{"ok": true, "cms_type": "wordpress", "status": "publish", "http_status": 201, "post_id": 123, "url": "https://example.com/hello-world/"}` / 示例（已发布，含发布 URL）
- On failure: `{"ok": false, "error": "<message>", "http_status": <code>}` printed to stderr with a non-zero exit code (never a raw traceback). / 失败时：错误 JSON 打印到 stderr 并以非零码退出（绝不抛裸堆栈）。
- The agent should record the response as a receipt: `outputs/cms-publish/<slug>.json`. / Agent 应把响应存为回执：`outputs/cms-publish/<slug>.json`。

## 验收项 / Acceptance Criteria

- [ ] Two-phase human confirmation is required before any live publish: Phase 1 — the user reviews the rendered content; Phase 2 — the user explicitly confirms "publish now". No `--publish` run without both. / 任何正式发布前必须两阶段人工确认：第一阶——用户审阅内容；第二阶——用户明确确认「现在发布」。缺少任一阶段不得执行 `--publish`。
- [ ] All secrets (`CMS_TYPE`, `CMS_API_URL`, `CMS_API_TOKEN`) are read from environment variables — nothing is hardcoded in the script or the skill. / 所有凭据从环境变量读取，脚本与 skill 中绝不硬编码。
- [ ] Graceful error handling: 429/5xx responses are retried with exponential backoff (respecting the `Retry-After` header); final failures exit non-zero with machine-readable JSON on stderr. / 错误处理优雅：429/5xx 按指数退避重试（遵循 `Retry-After` 响应头）；最终失败以非零码退出并在 stderr 输出可解析 JSON。
- [ ] Safe by default: with no flag the script creates a draft — a live publish requires the explicit `--publish` flag. / 默认安全：不加参数时只存草稿，正式发布必须显式传 `--publish`。
- [ ] The script prints exactly one JSON result to stdout including the published URL (or the draft status + ID). / 脚本向 stdout 输出唯一一个 JSON 结果，含发布 URL（或草稿状态 + ID）。
- [ ] Runs on Python 3.10+ using only the standard library (no third-party deps). / 仅用 Python 3.10+ 标准库运行（无第三方依赖）。

## 执行步骤 / Steps

1. Locate and read the content file; extract frontmatter (`title`, `slug`, `description`). / 定位并读取内容文件，提取 frontmatter。
2. Read `context/brand-voice.md` and `context/content-strategy.md`; run a final compliance check (no-go list, voice, funnel stage). / 读取 context 文档并做最终合规检查。
3. Verify `CMS_TYPE`, `CMS_API_URL`, `CMS_API_TOKEN` are present in the environment; ask the operator to set them if missing (never invent values). / 检查环境变量是否齐全，缺失时请运维补齐（绝不臆造）。
4. **Phase 1 approval**: show the user a preview (title, slug, excerpt, rendered content) and ask them to review. / **第一阶审批**：向用户展示预览（标题、slug、摘要、渲染后的内容）并请其审阅。
5. **Phase 2 approval**: ask for explicit confirmation to publish; if the user does not confirm, proceed with `--draft` only. / **第二阶审批**：请用户明确确认发布；未确认则仅执行 `--draft`。
6. Run the script: `python scripts/publish.py <file> --draft` or `--publish` (the latter only after both approvals). / 运行脚本（`--publish` 仅在两阶审批完成之后）。
7. Parse the stdout JSON; verify `"ok": true` and that the returned URL/status matches the request. / 解析 stdout JSON，核对 `"ok": true` 及返回的 URL/状态是否与请求一致。
8. Save the response as `outputs/cms-publish/<slug>.json` and report the published URL (or draft status) to the user. / 保存回执并汇报发布 URL（或草稿状态）。
9. On `"ok": false`, read the error JSON, fix the underlying cause (auth, payload, endpoint), and retry — do not blindly hammer the endpoint beyond the script's built-in backoff. / 失败时根据错误 JSON 修正根因（认证、载荷、端点）后再重试，不要超出脚本内置退避地盲目重复请求。

## 脚本 / Scripts

Publish (or save as draft) a content file via the CMS REST API: / 通过 CMS REST API 发布（或存草稿）：

```bash
python scripts/publish.py outputs/blog-post/<slug>.md --draft
python scripts/publish.py outputs/blog-post/<slug>.md --publish
python scripts/publish.py --help
```

Environment variables (secrets are injected here, never hardcoded): / 环境变量（凭据在此注入，绝不硬编码）：

```bash
export CMS_TYPE=wordpress            # wordpress | webflow | custom
export CMS_API_URL=https://example.com   # WordPress: site root; Webflow/custom: full REST endpoint
export CMS_API_TOKEN=<token>         # bearer token
```

No third-party dependencies — Python 3.10+ standard library only (`scripts/requirements.txt` is not needed). / 无第三方依赖，仅 Python 3.10+ 标准库（无需 `scripts/requirements.txt`）。凭据通过环境变量注入。

## 发布 / Publishing

This skill performs the write operation at the end of the pipeline. The target system is the configured CMS (WordPress / Webflow / custom). The approval node is strictly human: the agent must complete a two-phase confirmation (content review, then explicit publish consent) before invoking the script with `--publish` (AGENTS.md §4). The script itself defaults to `--draft`, so a missed confirmation can never silently go live. / 本 skill 执行流水线末端的写操作，目标系统为配置的 CMS（WordPress / Webflow / 自定义）。审批节点严格由人把关：Agent 必须先完成两阶段确认（内容审阅、明确发布同意）才能以 `--publish` 调用脚本（AGENTS.md §4）。脚本本身默认 `--draft`，即使漏掉确认也不会悄悄上线。
