# 素材源注册表

机器可读版本：`assets/connector-registry.json`。

| 来源 | 状态 | Key | 使用边界 | 降级 |
|---|---|---:|---|---|
| Mock | active | 否 | 测试数据，CC0 fixture | 始终可用 |
| Iconify | active | 否 | 仅自动使用 lucide/tabler/ph；按集合记录许可；清理SVG后栅格化PNG | 程序 PNG |
| Openverse | active | 可选 | 聚合元数据不担保授权，回原站核验 | Mock/跳过 |
| Pexels | configured-only | 是 | 保存摄影师和作品页，遵守平台条款 | Openverse/Wikimedia |
| Wikimedia Commons | active | 否 | 每个文件独立许可证和署名 | Openverse/Mock |

Unsplash、Pixabay、LottieFiles、Rive社区素材不作为默认自动导入源。不得批量镜像、绕过限制或把“可浏览”当作“可商用”。

真实连接器必须显式联网授权、超时、有限重试、来源/许可证字段、Mock 和失败降级。下载另受 `materials.py` HTTPS主机白名单与禁重定向限制。

原生 Emoji、线框和文字组件不属于外部素材：Emoji直接进入安全 HTML，不上传；线框组件使用内联 CSS，不依赖 SVG 或脚本。插画、背景和贴纸优先检索用户/外部许可素材，无合适候选时调用 `image_gen` 生成 PNG/JPG/GIF，再用 `materials.py register-local` 复制进文章包、登记并由发布器自动上传。
