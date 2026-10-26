# 微信兼容与降级

## 正文白名单

`section p span strong em br img table tbody thead tr td th blockquote a`。全部样式内联；正文无脚本、style/link、事件属性、外部字体和交互。

## 禁止 CSS

Flex/Grid、定位、浮动、transform、filter、animation/transition、clip/mask、背景 URL/gradient、CSS变量/calc、视口单位和负外边距。

## 图片与复杂节点

- 正文图片必须是本地登记资产或微信 CDN；真实草稿前上传并替换。
- SVG 保留源、清理后栅格化；不直接放正文。图标 SVG 同样必须先转 PNG。
- 原生 Emoji 和线框/引用/分割组件直接作为内联 HTML/CSS，不需要素材上传；Emoji不承载唯一信息。
- 正文 GIF 只在用户明确要求时尝试上传，必须登记 PNG/JPG 静态降级；上传接口拒绝 GIF 时自动回退。
- Mermaid/ECharts/Vega-Lite输出 SVG/PNG；Lottie/Rive输出 GIF/视频/首帧。
- 表格使用百分比宽度和内联边框；超宽组件转图或纵向重排。

## 深色与移动端

局部前景/背景对比正文至少4.5:1，大字至少3:1。375px无横向滚动。深色模拟只是风险筛查，最终必须在微信客户端预览。

## 发布保护

干跑 → 校验 → 上传正文图片 → 上传封面 → pending 锁 → 创建草稿。未知状态不重试。自动发布不在当前实现范围。
