# 微信安全组件

所有示例只说明DOM骨架。颜色、边距、边框和字号必须按文章视觉方案重设。

## 文章容器

```html
<section style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',Arial,sans-serif;color:#2b2b2b;font-size:15px;line-height:1.8;letter-spacing:.03em;background-color:#fbfaf7;padding:18px 16px;">...</section>
```

## 章节标题

```html
<section style="margin:34px 0 18px;border-left:3px solid #355c5a;padding:2px 0 2px 12px;"><p style="margin:0;color:#355c5a;font-size:12px;letter-spacing:.14em;">01</p><p style="margin:4px 0 0;color:#243332;font-size:18px;font-weight:700;line-height:1.45;">原文标题或已记录的新标题</p></section>
```

## 金句/核心观点

把原句从正文位置替换为组件，不要另抄一份。

```html
<section style="margin:24px 0;padding:20px 18px;background-color:#edf3f1;border-top:1px solid #9fb8b4;border-bottom:1px solid #9fb8b4;"><p style="margin:0;color:#24413e;font-size:17px;font-weight:600;line-height:1.75;">原句</p></section>
```

## 引用

```html
<blockquote style="margin:22px 0;padding:4px 0 4px 16px;border-left:2px solid #9b8464;color:#5e5549;"><p style="margin:0;font-size:14px;line-height:1.8;">原引用</p></blockquote>
```

## 两列数据

使用 `table style="width:100%;border-collapse:collapse" role="presentation"`，每个 `td` 设置明确百分比宽度、内边距、纯色背景和边框。不要用Flex模拟。

## 步骤与清单

使用 `p + span`，不要依赖 `ul/li` 默认样式。序号可新增，步骤文字必须来自原文。

## 图片

```html
<section style="margin:28px 0;"><img src="assets/inline-01.jpg" alt="准确描述" style="display:block;width:100%;height:auto;margin:0;" /><p style="margin:8px 0 0;color:#77716a;font-size:11px;line-height:1.55;text-align:center;">原文图注或经允许的说明</p></section>
```

## 文末

文末引导不能虚构账号名、二维码或往期文章。用户未提供时只做克制的结束分隔，不生成“点赞在看”等营销文案。

