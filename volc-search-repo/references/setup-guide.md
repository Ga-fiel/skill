# 火山引擎联网搜索 — 开通与排错

## 1. 开通与拿 Key

1. 打开 [联网搜索控制台](https://console.volcengine.com/search-infinity/web-search)，点「正式开通」
2. 进入 [API Key 管理](https://console.volcengine.com/search-infinity/api-key)
   - 「订阅套餐」标签：预付费套餐
   - 「按量后付费」标签：按量计费
   - 两者各发各自的 Key，**互不通用**
3. 创建后复制 Key，填进本 skill 的 `config.json` 的 `api_key` 字段

> 免费额度：每个火山账号每月 500 次，无论是否开通付费都优先消耗这部分。
> 默认限流 5 QPS，账号维度。

> ⚠️ **常见坑**：方舟 Ark 的 API Key 不能用于本接口。必须是「联网搜索」控制台里发出来的 Key。
> 另外 Coding Plan 用户是在 Ark 控制台「专属权益 → 联网搜索」里看 Key，那部分套餐有独立限制。

## 2. 认证方式

本 skill 走 **API Key + Bearer**，最简单：

```
POST https://open.feedcoopapi.com/search_api/web_search
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

如果要用 AK/SK（TOP 网关 `mercury.volcengineapi.com`，ServiceName=`volc_torchlight_api`），需要自己实现 HMAC-SHA256 V4 签名，本 skill 未实现。

## 3. 请求体字段速查

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `Query` | String | 必填，1~100 字符，**不支持多词搜索** |
| `SearchType` | String | 必填，`web` / `image` |
| `Count` | Number | web ≤ 50，image ≤ 5，默认 10 |
| `Filter.NeedContent` | Boolean | 只返回有正文的结果 |
| `Filter.NeedUrl` | Boolean | 只返回有落地页链接的结果 |
| `Filter.Sites` | String | 限定站点，`\|` 分隔，最多 20 个完整域名 |
| `Filter.BlockHosts` | String | 屏蔽站点，`\|` 分隔，最多 5 个 |
| `Filter.AuthInfoLevel` | Number | 0 不限 / 1 只要非常权威 |
| `TimeRange` | String | `OneDay` / `OneWeek` / `OneMonth` / `OneYear` / `YYYY-MM-DD..YYYY-MM-DD` |
| `QueryControl.QueryRewrite` | Boolean | 开启 Query 改写（增加耗时） |
| `ContentFormats` | String | `text` / `markdown` |
| `Industry` | String | `finance` / `game` / `gov` 行业搜索 |

`SearchType=image` 时额外支持 `Filter.ImageWidthMin` / `ImageHeightMin` / `ImageWidthMax` / `ImageHeightMax` / `ImageShapes`。

## 4. 返回字段速查（web 结果）

| 字段 | 说明 |
| --- | --- |
| `SortId` / `Title` / `SiteName` / `Url` | 基本展示信息 |
| `Snippet` | 约 200 字，**只适合列表展示，不建议给大模型** |
| `Summary` | 500~1000 字相关摘要，**推荐用于大模型** |
| `Content` | 站点正文 |
| `PublishTime` | ISO 时间，如 `2025-05-30T19:35:24+08:00` |
| `AuthInfoDes` | 非常权威 / 正常权威 / 一般权威 / 一般不权威 |
| `AuthInfoLevel` | 1~4，对应上面的顺序 |
| `RankScore` | 相关性得分 0~1 |
| `RuyiInfo` | 仅当 `SiteName` 为「火山如意」时出现（股票、天气、汇率等结构化卡片） |

## 5. 错误码

| 码 | 含义 | 处理 |
| --- | --- | --- |
| `10400` | ParamError 参数错误 | 检查 Query 长度、Count 上限、日期格式、字段类型 |
| `10401` | InvalidTopToken | TOP 网关 Token 无效 |
| `10402` | InvalidSearchType | 搜索类型非法，或未开通该类型 |
| `10403` | InvalidAccountId 权限错误 | 账号未开通搜索服务 / Key 不对 |
| `10406` | FreeQuotaExhausted | 免费额度用尽，去控制台开通付费 |
| `10409` | SearchPackageModeUnsupported | 订阅套餐不支持当前搜索类型 |
| `10410` | SearchPackageUnavailable | 套餐未开通或已到期 |
| `10412` | SearchPackageQuotaExhausted | 套餐剩余额度不足 |
| `10500` | InnerError | 兜底内部错误，等 2~3 秒重试 |
| `700429` | FreeRateLimitExceeded | 超出 QPS 限流（默认 5），降频重试 |
| `100013` | AccessDenied | 子账号缺少 `TorchlightApiFullAccess` 权限 |

## 6. 搜索技巧

- 结果不准：换简称/全称/别名；口语长句加 `--query-rewrite`
- 要最新：`--time-range OneDay`
- 要可信：`--auth-level 1`
- 结果太少：去掉语气词修饰词，只留核心实体词；或加大 `--count`
- 连试 2~3 次仍不理想：直接说证据不足，不要编
- 不适合场景：无时效要求的基础常识、纯计算、纯创作，不必搜

## 7. 安全

`config.json` 里是明文 Key。不要提交到 git，不要发到公开渠道。
如需换 Key，直接改这个文件，或临时用 `--api-key` 覆盖。
