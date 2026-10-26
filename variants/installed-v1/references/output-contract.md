# 文章包契约

## 目录

```text
wechat-output/YYYY-MM-DD-slug/
├── source.md
├── article-fragment.html
├── preview.html
├── article-package.json
├── design-brief.md
├── design-brief.json
├── changes.md
├── publish-result.json       # 仅发布后存在
└── assets/
```

## article-package.json

必填顶层字段：`schema_version`（当前为1.0）、`title`、`slug`、`created_at`、源文件/正文/预览路径、`design`、`editing_policy`、`assets` 和 `publishing`。

`design` 包含赛道、视觉概念、三色以内的色板和组件列表。`publishing` 包含封面资产ID、作者、摘要、评论设置和状态。

## 素材角色

`cover`、`inline`、`illustration`、`texture`、`ornament`、`qr`。封面角色只能有一个主资产；正文引用的本地图片必须能在素材数组中找到。

## 变更清单

`changes.md` 必须区分拆段、增加结构标题、原句组件升级、列表结构化、图片插入。若没有结构改动，明确写“无结构性改动”。

## 发布状态

`publishing.status` 使用 `not_started`、`dry_run_ready`、`pending_unknown`、`draft_created` 或 `failed`。不得写入token、AppSecret或完整认证URL。

## 打开预览

浏览器可能限制 `file://` 页面的富文本剪贴板。优先运行 `scripts/serve_preview.py <文章包>`，它只绑定 `127.0.0.1`，关闭终端或按Ctrl+C即停止。
