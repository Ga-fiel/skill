---
name: volc-search
description: 用火山引擎（豆包搜索 Custom 版）联网搜索 API 代替默认 web_search。仅当用户明确要求「/volc-search」「用火山搜」「用豆包搜索」时才使用；默认情况下不要主动调用，也不要因为需要联网就自动切到本 skill。支持网页搜索、图片搜索、时间范围、权威来源过滤、站点限定、Query 改写。
---

# volc-search — 火山引擎联网搜索

用火山引擎「豆包搜索 Custom 版」的 HTTP 接口做联网搜索，返回网页或图片结果。

## 触发条件（严格）

**只在用户明确点名时才用**：

- 用户输入 `/volc-search ...`
- 用户说「用火山搜」「用火山引擎搜」「用豆包搜索」「走火山引擎」

**不要自动使用**。以下情况仍走默认 `web_search`，即使明显需要联网：

- 用户没点名本 skill
- 用户只是普通提问、需要查资料、需要核实事实

换句话说：本 skill 是**显式点名才启用的替代通道**，不是全局默认搜索引擎。

## 用法

脚本通过 `python` 运行（Windows 上是 `D:\PRtool\python\python.exe`，`Get-Command python` 能找到）。只用 Python 标准库 `urllib`，不需要 `pip install` 任何东西。

```
python <skill目录>/scripts/volc_search.py "搜索词" [参数...]
```

示例：

```
python volc-search\scripts\volc_search.py "华为发布会 2026"
python volc-search\scripts\volc_search.py "AI 芯片 出口管制" --time-range OneWeek --auth-level 1
python volc-search\scripts\volc_search.py "某公司 财报" --sites eastmoney.com|cls.cn
python volc-search\scripts\volc_search.py "小米 SU7" --type image --count 3
python volc-search\scripts\volc_search.py "这个新出的框架好不好用" --query-rewrite
python volc-search\scripts\volc_search.py "某事件 来龙去脉" --time-range 2025-01-01..2026-10-28
```

## 参数

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `query` | 搜索词，1~100 字符，**不支持多词搜索**（会把整串当一个 query 发过去，自行精简关键词） | 必填 |
| `--type` / `-t` | `web` 网页 / `image` 图片 | `web` |
| `--count` / `-c` | 返回条数，web ≤ 50，image ≤ 5 | 10 |
| `--time-range` | `OneDay` / `OneWeek` / `OneMonth` / `OneYear` / `YYYY-MM-DD..YYYY-MM-DD` | 不限制 |
| `--auth-level` | `1` = 只要非常权威来源（gov/央媒/官媒等），`0` = 不限 | 0 |
| `--sites` | 限定站点，完整域名，`\|` 分隔，最多 20 个 | 无 |
| `--block-hosts` | 屏蔽站点，`\|` 分隔，最多 5 个 | 无 |
| `--query-rewrite` | 开启 Query 改写，适合口语化长句 | 关闭 |
| `--industry` | `finance` / `game` / `gov` 行业搜索 | 无 |
| `--need-content` | 只返回带正文的结果，并输出正文 | 关闭 |
| `--format` | `text`（人读） / `json`（进一步处理） | `text` |
| `--api-key` | 临时覆盖配置文件里的 Key | 读配置 |

## 自然语言 → 参数映射

| 用户说法 | 参数 |
| --- | --- |
| 「要最新的」「今天的」 | `--time-range OneDay` |
| 「最近一周」「这周」 | `--time-range OneWeek` |
| 「最近一个月」 | `--time-range OneMonth` |
| 「去年到今年」 | `--time-range 2025-01-01..2026-10-28` |
| 「只要官方/权威的」「gov 的」 | `--auth-level 1` |
| 「只看某网站」 | `--sites 域名` |
| 「找图片/海报/logo」 | `--type image` |
| 口语化长问题、结果不准 | `--query-rewrite` |
| 金融/游戏/政务话题 | `--industry finance` / `game` / `gov` |

## 结果怎么用

- 优先读 `Summary` 字段（500~1000 字的相关摘要，适合大模型）。`Snippet` 只有约 200 字，信息可能残缺，不要只靠它。
- 每条结果带 `AuthInfoDes`（非常权威 / 正常权威 / 一般权威 / 一般不权威），可信度不同，回答时按这个权重取舍。
- 回答里标注来源：站点名 + 标题 + URL（markdown 链接）。
- 搜索结果不足以回答时坦率说明，不要编。

## 失败怎么处理

| 现象 | 处理 |
| --- | --- |
| 鉴权失败（`10403` / `invalid_api_key` / 401） | 提示 Key 位置 `config.json`，并给控制台链接 |
| `10406` / `10412` 额度用尽 | 告诉用户额度用完，建议改回默认 `web_search` 或去控制台充值 |
| `700429` / 429 限流 | 降频重试一次（等待 2~3 秒），仍失败则告知 |
| `10500` 内部错误 | 重试一次 |
| `10400` 参数错误 | 检查 query 长度、count 上限、日期格式 |

**兜底**：火山接口连续失败 2 次（额度/限流/鉴权以外的问题）后，改走默认 `web_search` 补位，并在回答里说明「火山搜索不可用，已回退到默认搜索」。

## 配置文件

`config.json`（与 `SKILL.md` 同级）：

```json
{
  "api_key": "在这里填 API Key",
  "endpoint": "https://open.feedcoopapi.com/search_api/web_search",
  "default_count": 10,
  "timeout": 30
}
```

- `api_key`：火山引擎联网搜索控制台里的 API Key（**不是**方舟 Ark 的 Key，两者不通用）
- 也支持环境变量 `WEB_SEARCH_API_KEY` 或 `VOLC_SEARCH_API_KEY`，优先级：`--api-key` > 环境变量 > `config.json`
- 这个文件含密钥，**不要提交到任何仓库，不要贴到公开的地方**

更多错误码、开通步骤见 `references/setup-guide.md`。
