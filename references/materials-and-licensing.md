# 素材与许可证

## 默认优先级

1. 用户明确指定且确认有权使用的素材。
2. 用户个人素材仓库。
3. 用户本次上传与参考资料。
4. Openverse/Pexels/Wikimedia等许可明确的外部素材；逐项核验。
5. AI原创封面、插画与纹理；记录生成工具、日期和提示词。
6. Iconify白名单图标或程序图形；发布前转为PNG。
7. 可画/Figma人工精修导出。

技能自带 `assets/original-ornament.svg/png` 作为原创、可安全复用的轻量分隔母题；可按文章配色修改SVG后重新栅格化，但不要让所有文章都默认使用它。

## 禁止事项

- 禁止抓取百度图片、公众号文章、Pinterest、花瓣、站酷等搜索/作品页作为素材库。
- 禁止绕过登录、下载限制、水印或付费墙。
- 禁止把“免费浏览”解释为“可商用”。
- 禁止批量镜像Unsplash、Pixabay、Storyset或可画素材。
- 禁止使用许可证未知、作者未知或仅限编辑用途的素材做商业宣传。

## 提供商规则

- Openverse：API是检索索引，不替素材本身担保；读取每条结果的许可证、作者与来源页。
- Pexels：使用官方API密钥；在素材清单提供Pexels链接，尽可能署名摄影师。
- Iconify：只自动使用 `lucide`、`tabler`、`ph` 三个白名单集合；仍保存集合许可证。
- Unsplash：API要求热链、下载追踪与署名，和微信本地转存流程冲突；本技能不提供自动下载适配器。
- Pixabay/Storyset：不提供网页抓取；只有未来明确接入官方API并实现条款要求后才能自动化。

## 素材记录字段

每个 `article-package.json.assets[]` 至少包含：`id`、`role`、`local_path`、`provider`、`creator`、`source_url`、`license`、`license_url`、`credit`、`accessed_at`、`modifications`、`wechat_url`。

AI或技能原创素材使用 `provider: generated|original`，并写明生成工具/脚本；第三方素材缺少来源或许可证时，校验必须失败。
