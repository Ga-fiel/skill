# .DSH Volc Search

火山引擎（豆包搜索 Custom 版）联网搜索 skill，用来替换 DSH 默认的 `web_search`。

> 仅在显式点名时触发（`/volc-search`、「用火山搜」等），默认不自动启用。

## 特性

- 纯 Python 标准库实现，**零第三方依赖**
- 支持网页搜索、图片搜索
- 支持时间范围过滤（近一天、一周、一月、一年，或自定义日期区间）
- 支持权威来源过滤（gov、央媒、官媒等）
- 支持站点限定、站点屏蔽
- 支持 Query 改写（口语化长问自动转搜索式）
- 支持行业搜索（金融、游戏、政务）

## 目录结构

```
volc-search/
├── SKILL.md                  技能说明与参数文档
├── config.example.json       配置模板
├── .gitignore
├── references/
│   └── setup-guide.md        开通步骤、字段速查、错误码表
└── scripts/
    └── volc_search.py        搜索脚本
```

## 安装

1. 把整个文件夹放到 DSH 的 skills 目录下：

   ```
   ~/.dsh/skills/volc-search/
   ```

2. 复制配置模板并填入你的 API Key：

   ```bash
   cp config.example.json config.json
   ```

   ```json
   {
     "api_key": "你的API Key",
     "endpoint": "https://open.feedcoopapi.com/search_api/web_search",
     "default_count": 10,
     "timeout": 30
   }
   ```

   也可以把 Key 单独写成文本文件，然后在 `config.json` 里指定：

   ```json
   { "key_file": "key" }
   ```

   此时 `key` 文件里只放 Key 本身，一行即可。

3. Key 获取地址：[联网搜索控制台 - API Key 管理](https://console.volcengine.com/search-infinity/api-key)

   > ⚠️ 必须是「联网搜索」的 Key。方舟 Ark 的 API Key **不通用**。

## 使用

### 通过 skill 调用

在对话里输入：

```
/volc-search 华为发布会 2026
```

### 直接运行脚本

```bash
python scripts/volc_search.py "华为发布会 2026"
python scripts/volc_search.py "AI 芯片 出口管制" --time-range OneWeek --auth-level 1
python scripts/volc_search.py "小米 SU7" --type image --count 3
python scripts/volc_search.py "某公司 财报" --sites eastmoney.com|cls.cn
python scripts/volc_search.py "这个新出的框架好不好用" --query-rewrite
python scripts/volc_search.py "某事件" --format json
```

### 参数

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `query` | 搜索词，1~100 字符 | 必填 |
| `--type` / `-t` | `web` 网页 / `image` 图片 | `web` |
| `--count` / `-c` | 返回条数，web ≤ 50，image ≤ 5 | 10 |
| `--time-range` | `OneDay` / `OneWeek` / `OneMonth` / `OneYear` / `YYYY-MM-DD..YYYY-MM-DD` | 不限 |
| `--auth-level` | `1` = 只要非常权威来源 | 0 |
| `--sites` | 限定站点，`\|` 分隔，最多 20 个 | 无 |
| `--block-hosts` | 屏蔽站点，`\|` 分隔，最多 5 个 | 无 |
| `--query-rewrite` | 开启 Query 改写 | 关闭 |
| `--industry` | `finance` / `game` / `gov` | 无 |
| `--need-content` | 只返回带正文的结果并输出正文 | 关闭 |
| `--format` | `text` / `json` | `text` |
| `--api-key` | 临时覆盖配置里的 Key | 读配置 |

## 免费额度与限制

- **每月 500 次**免费额度，按火山引擎**主账号**维度统计
- 每月 1 日重置
- 与 Global 版共用额度，不区分搜索类型、不区分付费方式
- 只要有免费额度就**优先扣免费额度**
- 默认限流 **10 QPS**，账号维度，可提工单扩容
- 超出额度后按量后付费

## 错误码

| 码 | 含义 | 处理 |
| --- | --- | --- |
| `10400` | 参数错误 | 检查 Query 长度、Count 上限、日期格式 |
| `10402` | 搜索类型非法 | 检查 `--type` 与开通情况 |
| `10403` | 权限错误 | Key 不对或未开通服务 |
| `10406` | 免费额度用尽 | 控制台开通付费 |
| `10412` | 套餐额度不足 | 充值或换后付费 Key |
| `10500` | 内部错误 | 等待 2~3 秒重试 |
| `700429` | 触发限流 | 降频后重试 |

完整列表见 [references/setup-guide.md](references/setup-guide.md)。

## 安全提示

**不要提交你的 API Key。**

- `config.json` 和 `key` 文件已在 `.gitignore` 中忽略
- 如果曾经误提交过 Key，立刻到控制台**吊销并重新创建**
- 推荐用环境变量 `VOLC_SEARCH_API_KEY` 或 `WEB_SEARCH_API_KEY` 传入

## 协议

MIT
