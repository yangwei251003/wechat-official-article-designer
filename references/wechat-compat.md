# 微信兼容硬约束

## 输出边界

- 预览外壳可以使用JavaScript和普通网页CSS；`#wechat-content` 内的文章正文不得包含脚本、样式表或交互。
- 文章正文只使用 `section`、`p`、`span`、`strong`、`em`、`br`、`img`、`table`、`thead`、`tbody`、`tr`、`th`、`td`、`blockquote`、`a`。
- 所有视觉样式必须内联。不要依赖 `class`、CSS变量、媒体查询或继承才能正确显示。
- 多列只用表格；不要使用Flex、Grid、浮动或定位。

## 禁用CSS

禁止 `display:flex/grid`、`position`、`float`、`transform`、`filter`、`backdrop-filter`、`animation`、`transition`、`clip-path`、`mask`、`background-image`、`linear-gradient`、`radial-gradient`、`var()`、`calc()`、负边距和视口单位。

可用属性以字体、颜色、纯色背景、边框、圆角、内外边距、行高、字距、文本对齐、宽高和 `max-width` 为主。阴影不是关键结构；即使使用也必须允许被微信删除而不影响阅读。

## 字体与正文

- 字体栈：`-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",Arial,sans-serif`。
- 正文建议14–16px、行高1.72–1.85、颜色不使用纯黑。
- 不强制两端对齐；中文移动端长文默认左对齐，只有内容确实需要整齐边缘时使用 `text-align:justify`。
- 不通过新增空格改变原文；字距使用 `letter-spacing`。

## 图片与背景

- 文章图片使用真实 `<img>`，设置 `width:100%;height:auto;display:block`。
- API发布前，正文图片必须上传为微信返回的URL；复制模式下，非微信CDN图片只视为待转存素材。
- 不使用data URL、本地文件URL或CSS背景图作为最终发布资产。
- SVG保留为源文件即可，发布版本必须转成PNG/JPG。
- 全页背景只用浅色纯色。复杂纹理作为低信息密度的独立图片，不能承载正文可读性。

## 深色模式

- 不能假设微信完全保留或完全反转颜色。
- 保持正文文字与其局部背景至少4.5:1；大字至少3:1。
- 避免纯白文字压在透明图上、透明PNG依赖白底、极浅边框承载唯一层级。
- 交付前在预览页切换深色模拟，并在微信客户端做最终预览。

## 发布前清单

1. 正文无脚本、style/link/iframe/video/svg标签。
2. 无Flex/Grid/定位/渐变/背景图。
3. 所有图片可达或已上传微信。
4. 文章在375px宽度无横向滚动。
5. 标题、数据和引用即使去掉装饰仍可理解。
6. 浅色和深色模式均能读清正文。
