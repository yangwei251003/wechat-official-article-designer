# Article Schema 2.0

权威文件：`assets/article-schema-v2.json`。

顶层包含：版本、文档 ID、元数据、目标、内容章节/节点、设计 Token、素材、锁定、历史、微信降级和版权状态。高设计文章在 `design` 中额外记录 `mode`、`design_read`、三只 `controls`、`visual_concept`、`rhythm_families` 与 `quality_gates`。

节点类型：`text`、`image`、`chart`、`component`、`video`、`table`。每个节点必须含 ID、锁定状态和 provenance。复杂节点应带 `fallback`。

规则：

1. AI 生成或迁移的 JSON 先校验再落盘/编译。
2. `schema_version` 当前为 `2.0`。
3. v1 `article-package.json` 继续作为交付清单，通过 `article_file` 关联 v2。
4. 迁移使用 `article_schema.py migrate-v1`；不得手工假装版本号变化。
5. 结构修改使用 `revisions.py`，锁定冲突必须失败。
6. `design.mode=high-design` 时必须运行 `design_quality.py`；Schema 合法不等于审美门槛通过。
