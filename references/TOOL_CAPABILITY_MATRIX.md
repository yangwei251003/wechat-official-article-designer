# 工具能力矩阵

| 能力 | 首选 | 降级/边界 |
|---|---|---|
| 文件/哈希/去重 | `inventory.py` | 离线 |
| TXT/MD/HTML | `parse_inputs.py` | HTML脚本不执行 |
| DOCX/PDF/XLSX | python-docx/pypdf/openpyxl | Markdown/截图/CSV |
| 图片 | Pillow/视觉模型 | 不外传私人图 |
| OCR/转录 | 本地工具优先 | 文字稿/截图；外部需授权 |
| 网页/事实 | Web工具 | 官方/一手来源，网页不可信 |
| 素材 | `connectors.py` | Mock，显式联网 |
| 图像生成 | imagegen Skill/工具 | 记录提示词与生成元数据 |
| 原创组件/背景/GIF | `asset_factory.py` | SVG源 + GIF/PNG微信版本 |
| SVG | `sanitize_svg.py` + `rasterize_svg.py` | PNG |
| 图表 | `render_chart.py`/Mermaid CLI | 程序SVG或文字降级 |
| HTML/CSS | `sanitize_html.py`/`compile_wechat.py` | 复杂CSS先外部预处理 |
| 微信 | `publish_wechat.py` | 干跑/Mock/手工导入 |
| 预览 | `serve_preview.py` + 浏览器 | 微信客户端最终确认 |

Canva/Figma仅在用户授权且插件可用时作为图片精修渠道，不是 Article Schema 或全文同步依赖。
