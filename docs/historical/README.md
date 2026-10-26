# 微信公众号 AI 内容与视觉设计超级 Skill

版本：2.2.0

这是一个可被 Codex 调用的模块化 Skill。它把一句主题、完整文章或多格式资料转为可审阅、可追溯、可测试、可导出到微信公众号的文章包；它不是网站、SaaS 或自由画布编辑器。

## 能做什么

- 盘点 TXT/Markdown/HTML/DOCX/PDF/CSV/XLSX/图片/SVG/音视频，保存哈希和降级状态。
- 先完成内容策略、来源分类、审阅与锁定，再进入视觉设计。
- 生成三套布局、组件、图片策略明显不同的 Design Brief。
- 强制记录 Design Read、三只视觉旋钮和单一视觉母题；高设计成品必须通过原创资产、节奏与旧图隔离门槛。
- 按媒介处理 Emoji、Iconify 图标、线框组件、插画、背景和 GIF；图像型资产自动登记并上传，原生组件直接编译为安全 HTML。
- 建立个人素材索引，按主题、品牌、版权、清晰度和复用惩罚排序。
- 通过 Mock、Openverse、Pexels、Iconify、Wikimedia 统一接口检索候选素材。
- 生成 Article Schema 2.0，支持 v1 迁移、修改记录和版本回退。
- 清理/内联 HTML 与 CSS，清理 SVG，渲染静态图表接口，编译微信安全 HTML。
- 生成版权、署名、兼容性、安全与测试报告。
- 默认干跑微信草稿；只有明确授权后才连接真实官方 API。

## 安装与环境

Python 3.11+。核心脚本尽量使用标准库；多格式与渲染能力使用 `requirements.txt` 中的轻量依赖。

```powershell
python -m pip install -r requirements.txt
python scripts/self_test.py
python -m unittest discover -s tests -v
```

把本目录放入 Codex Skill 搜索路径，或保持在工作区并显式使用 `$wechat-official-article-designer`。复制 `.env.example` 到仅本地使用的 `.env` 时，不要提交真实凭证；当前脚本只读取环境变量，不自动加载 `.env`。

## 快速使用

### 1. 只有一个主题

> 使用 `$wechat-official-article-designer`，围绕“AI 如何帮助小团队做用户研究”策划并设计一篇公众号文章。目标读者是创业团队，允许联网核实事实，不使用权属不明素材，输出 HTML、Markdown、封面任务和版权报告。

Skill 会先补齐少量高价值信息或记录默认假设，完成内容方案与草稿审阅，再生成视觉方向和文章包。

### 2. 上传完整文章与素材

> 使用 `$wechat-official-article-designer` 处理我上传的 DOCX、Logo 和三张产品图。正文数字和产品名称全部锁定，沿用 Logo 主色，个人素材优先，生成微信兼容 HTML、预览、图片包和素材来源报告。

### 3. 修改已有推文

> 使用 `$wechat-official-article-designer` 修改这个已有文章包：只重做第二节的信息层级和配图，不改标题、第一节、数据和结尾；保留变更记录并重新运行兼容与版权检查。

## 命令行工作流

```powershell
# 资料盘点与解析
python scripts/inventory.py input --output workspace/inventory.json
python scripts/parse_inputs.py input/article.docx --root input --output workspace/normalized/article.json

# Article Schema、锁定与版本
python scripts/article_schema.py scaffold source.md --title "文章标题" --output article.json
python scripts/article_schema.py validate article.json
python scripts/revisions.py revise-text article.json node-2 "已授权的新文字" --actor user --output article-v2.json
python scripts/revisions.py rollback article-v2.json 1 --output article-restored.json

# 设计与素材
python scripts/design_brief.py "文章标题" --track "知识科普" --palette "#101522" "#FF5B45" "#C8FF4A" --output design-brief.json
python scripts/library.py build user-library --output user-library/library-index.json
python scripts/library.py search user-library/library-index.json "亲子 儿童节"
python scripts/connectors.py search --provider mock --query "science" --output research/mock-assets.json
# 只有得到用户联网授权后：
python scripts/connectors.py search --provider openverse --query "science" --allow-network --output research/openverse.json
# 外部素材不贴合时，自主创作可编辑SVG、微信GIF/PNG、背景与组件
python scripts/asset_factory.py "用户研究：在噪声中捕捉行为信号" --output-dir package/assets --palette "#101522" "#FF5B45" "#C8FF4A"
# 规划 Emoji、图标、线框、插画和背景；生成 imagegen 任务清单与微信安全组件
python scripts/visual_elements.py "用户研究：在噪声中捕捉行为信号" --output-dir package/assets --palette "#101522" "#FF5B45" "#C8FF4A"
# 从许可明确的 Iconify 图标集导出微信 PNG
python scripts/materials.py icon --name "lucide:search" --output package/assets/search.svg --wechat-png package/assets/search.png --package-dir package
# 登记 imagegen 或用户提供的最终位图，发布时自动上传
python scripts/materials.py register-local --input generated-image.png --package-dir package --output assets/generated-image.png --role illustration

# 编译、构建、校验与打包
python scripts/compile_wechat.py article.json --output-dir build
python scripts/build_package.py --input source.md --output-dir package
python scripts/render_preview.py package/article-fragment.html --title "文章标题" --style-summary "本篇视觉概念" --output package/preview.html
python scripts/design_quality.py package --output package/design-quality-report.json
python scripts/validate_package.py package --json --output package/compatibility-report.json
python scripts/license_report.py package/article-package.json --json-out package/license-report.json --markdown-out package/license-report.md
python scripts/serve_preview.py package
python scripts/export_package.py package package.zip
```

## 输出结构

新构建文章包包含：

```text
package/
├── source.md
├── article.json                 # Article Schema 2.0
├── article-fragment.html        # 微信正文片段
├── preview.html
├── article-package.json         # v1 兼容清单
├── design-brief.md
├── design-brief.json            # 三套视觉方向与资产任务
├── changes.md
├── compatibility-report.json
├── design-quality-report.json   # 高设计门槛；基线草稿不会通过
├── license-report.json
├── license-report.md
└── assets/
```

## 微信草稿

先在没有凭证的情况下干跑：

```powershell
python scripts/publish_wechat.py package
```

独立 Mock 服务：

```powershell
python scripts/mock_wechat_server.py --scenario success
```

真实写入必须由用户明确授权本次执行，并通过环境变量提供 `WECHAT_APP_ID`、`WECHAT_APP_SECRET`。随后才可运行：

```powershell
python scripts/publish_wechat.py package --commit
python scripts/verify_wechat_draft.py package
# 明确要求正文保留GIF动效时；接口拒绝会自动回退到已登记的PNG/JPG首帧
python scripts/publish_wechat.py package --commit --allow-gif
```

脚本只创建草稿，不群发。出现 `publish-pending.json` 表示请求结果未知，必须先到公众号后台人工核对，不能自动重试。

## 测试与评估

```powershell
python -m unittest discover -s tests -v
python scripts/self_test.py
python scripts/run_evals.py evals/scenarios.json --report evals/latest-report.json
python -m compileall -q scripts tests
python scripts/security_audit.py . --output docs/SECURITY_REPORT.json
```

`evals/scenarios.json` 覆盖提示词要求的 20 个代表性场景，并增加“旧图不得进入新设计”和“高设计不得只交付基线”两项场景，共 22 项。真实 API、真实微信账号和外部上传不进入自动测试。

## 手工验收

1. 打开 `preview.html`，检查 375/390/430px。
2. 切换浅色/深色模拟，确认正文和局部背景可读。
3. 复制富文本到微信公众号编辑器，确认样式与图片转存。
4. 在微信客户端预览标题、封面、摘要、表格、链接与长文节奏。
5. 对照 `changes.md` 检查锁定内容、数字、人名和引用。
6. 对照 `license-report.md` 完成署名与人工版权确认。
7. 高设计任务确认 `design-quality-report.json` 通过；`build_package.py` 无自定义 fragment 的输出仅作内容核对草稿。

详细清单见 `docs/MANUAL_ACCEPTANCE.md`。

## 故障排查

- DOCX/PDF/XLSX 解析器缺失：安装 `requirements.txt`，或另存为 Markdown/CSV。
- PDF 没有文本：提供页面截图或启用经授权的 OCR；脚本不会伪造正文。
- ffmpeg/ffprobe 缺失：提供文字稿/关键帧，或本地安装后重试。
- Mermaid CLI 缺失：保留源文件，使用 Mock/程序静态图或人工渲染。
- Pexels 缺 Key：改用 Mock/Openverse/Wikimedia，或设置 `PEXELS_API_KEY`。
- 外部素材下载被拒绝：主机不在安全白名单；人工核验来源，不要放宽为任意 URL。
- 微信 API 报错：查看 errcode、账号权限和 IP 白名单，不要打印 Secret。

## 已知限制

- 本示例已在一套用户授权的真实公众号凭证下完成 Token、图片、封面、草稿创建和草稿回读验证；其他账号仍需各自完成权限和 IP 白名单联调。
- 当前 CSS 内联器支持简单标签、`.class` 和 `#id` 选择器，不是完整浏览器 CSS 引擎。
- PDF 主要读取文本层；扫描件 OCR、音视频转录与真实 ECharts/Vega-Lite 渲染依赖外部工具或授权服务。
- 外部素材元数据不是法律意见；未知、自定义、ShareAlike 与人物/商标素材仍需人工确认。
- 微信客户端行为会变化，任何“100%兼容”表述都不可靠，发布前必须真实预览。

更多实现状态与边界见 `docs/STATUS.md` 和 `docs/KNOWN_LIMITATIONS.md`。
