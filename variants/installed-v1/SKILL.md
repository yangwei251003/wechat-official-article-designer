---
name: wechat-official-article-designer
description: Design, package, validate, and safely deliver polished WeChat Official Account articles from pasted text, Markdown, TXT, HTML, or document content. Use when the user asks for 微信公众号排版、微信推文设计、公众号HTML、文章配图/封面/插画、可画或Figma素材任务包、微信兼容性检查，或将成品写入微信公众号草稿箱。 Preserve facts and source meaning, permit explicitly logged structural edits, generate content-specific visual direction and licensed/original assets, output copyable inline-style HTML, and optionally upload images plus a draft through the official WeChat API.
---

# 微信公众号全链路视觉排版

将文章变成内容驱动、可审计、可复制并可写入微信草稿箱的成品。优先保证原文事实与微信兼容，再追求视觉表达。

## 必读路由

每次生成或检查文章前，读取：

- `references/wechat-compat.md`：微信安全标签、CSS和深色模式底线。
- `references/visual-system.md`：从内容推导视觉方向的方法。
- `references/components.md`：安全组件结构与使用密度。
- `references/output-contract.md`：文章包文件和JSON约定。

按任务需要再读取：

- 搜图、下载或生成素材：`references/materials-and-licensing.md`。
- 对标优秀案例：`references/case-benchmark.md`。
- 使用可画或Figma：`references/external-tools.md`。
- 上传微信草稿：`references/wechat-api.md`。

## 工作流

### 1. 保存输入并锁定编辑边界

将用户原文原样保存为 `source.md`。接受粘贴文字、Markdown、TXT、HTML和可读取的文档。遇到DOCX/PDF等二进制文档时，先使用对应文档技能提取正文与媒体标记，再进入本流程；不要把二进制文件直接传给构建脚本。

允许：拆段、增加结构性小标题、将原句原位升级为金句、把既有列表映射为编号组件。禁止：改变事实、观点、数字、人名、引用、因果、语气结论或叙述顺序。不要重复摘抄金句；用组件替代原句所在位置。

把每一项结构变化写入 `changes.md`。未经用户明确授权，不做润色、扩写、删减或事实补充。

### 2. 建立内容画像与案例对标

识别赛道、读者、信息形状、情绪、篇幅、阅读速度、数据/步骤/引用和媒体需求。需要新鲜案例时联网调研同赛道3–5篇公开文章，只提炼留白、层级、节奏、图文比例和色彩逻辑，不复制具体模板或素材。联网不可用时使用 `case-benchmark.md` 的种子矩阵并标注为离线参考。

### 3. 现场设计

为当前文章定义：一句视觉概念；主色、辅助色、点缀色（最多三种）；字号层级与阅读节奏；2–5种组件及其出现位置；一处视觉记忆点；封面、正文插画、纹理和装饰的素材需求。

视觉必须随文变化，不套固定品牌皮肤。自定义字体不能进入微信正文；只用系统字体栈，通过构图、层级、色块和图片形成身份感。

### 4. 规划并取得素材

优先调用可用的图像生成能力制作统一风格的封面、插画和纹理；先向用户展示生成提示词并确认，再生成并保存到文章包 `assets/`。实景需求使用正规API素材，禁止抓取搜索结果页或绕过平台限制。

运行 `scripts/materials.py` 搜索Openverse/Pexels或获取许可白名单内的Iconify图标；使用 `--package-dir` 可同步登记到文章包。每个第三方素材必须记录来源页、作者、许可证、访问日期和署名。把SVG通过 `scripts/rasterize_svg.py` 转成PNG后再用于文章。

若用户希望外部精修，生成 `design-brief.md/json`：可画给出模板检索词、画布、文字安全区、配色、构图和PNG导出命名，不声称可画能直接同步全文；Figma工具可用时创建个人草稿中的设计Frame并导出PNG，权限失败时交付同一任务包。

### 5. 生成微信安全正文

使用 `section`、`p`、`span`、`strong`、`img`和必要的`table`。全部文章样式写入 `style`，不依赖class。禁止脚本、外部字体、Flex/Grid、定位、变换、滤镜、动画、渐变和CSS背景图。

复杂背景与SVG装饰必须变成真实PNG图片。页面背景以纯色、边框、浅色块和留白为主。首条封面输出900×383；同时准备900×500正文引导图和方形安全裁切。

可先由AI写出 `article-fragment.html`，再运行：

```powershell
python <skill>/scripts/build_package.py --input source.md --fragment article-fragment.html --changes changes.md --output-root .
```

没有自定义fragment时，脚本会生成保守但可用的基线版式。

### 6. 强制校验

运行：

```powershell
python <skill>/scripts/validate_package.py <article-package-directory>
```

所有错误必须修复。重点确认：原文段落按顺序完整出现、改动有记录、无禁用标签/CSS、本地图片存在、第三方素材许可证齐全、低对比颜色已处理。警告要向用户解释，不得隐藏。

运行 `python <skill>/scripts/serve_preview.py <article-package-directory>`，通过仅绑定本机的临时地址打开预览，避免 `file://` 剪贴板权限不一致。检查375/390/430px以及浅色/深色模拟。复制模式若发现本地、data或非微信CDN图片，必须显示风险提示。

### 7. 交付或写入草稿

默认交付完整文章包和可点击的 `preview.html`。用户要求微信草稿时，先读取 `wechat-api.md`，确认本机环境变量已配置，然后先执行干跑：

```powershell
python <skill>/scripts/publish_wechat.py <article-package-directory>
```

只有用户明确要求本次写入草稿，才追加 `--commit`。该脚本只创建草稿，永不群发。若上一次草稿请求状态未知，禁止自动重试，先让用户在后台核对并显式清除pending状态。

## 交付说明

向用户报告视觉方向、结构改动、素材来源、校验结果、复制风险和草稿ID（如有）。不要暴露AppSecret、access token或完整请求头。不要用“100%兼容”措辞；提醒最终在微信客户端浅色/深色模式预览后发布。
