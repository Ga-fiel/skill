# DSH Skills

我在用的 DSH（DeepSeek Harness）自定义 skill 合集。

每个一级目录是一个独立 skill，按 DSH 的 skill 规范组织（含 `SKILL.md`），直接复制进 `~/.dsh/skills/` 即可使用。

## 目录

| Skill | 说明 |
| --- | --- |
| [volc-search](volc-search/) | 用火山引擎（豆包搜索 Custom 版）替代默认 `web_search`，支持网页/图片搜索、时间范围、权威源过滤 |

## 安装方式

1. 把需要的 skill 文件夹整个复制到 DSH 的 skills 目录：

   ```
   ~/.dsh/skills/volc-search/
   ```

2. 按该 skill 的 `README.md` 或 `SKILL.md` 配置 API Key 等凭据。
3. 重启 DSH 会话，skill 会自动出现在可用列表里。

## 通用约定

- **显式触发**：这里的 skill 默认都不自动启用，需要你点名或输入 `/skill-name` 才会生效，避免抢占默认行为。
- **零依赖优先**：脚本尽量只用标准语言自带库，不需要额外安装环境。
- **凭据不入库**：所有仓库都不提交真实 API Key，只提供 `*.example` 模板，密钥由使用者自行配置。

## 安全提示

⚠️ 每个 skill 目录里都有 `.gitignore`，用于忽略 `key`、`config.json` 等凭据文件。**在你自己的仓库里新增 skill 时，请保持这个习惯**，不要把 Key 提交上去。

如果不慎提交过 Key，请立刻到对应平台的控制台撤销并重建。

## License

MIT
