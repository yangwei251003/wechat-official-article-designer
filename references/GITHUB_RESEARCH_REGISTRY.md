# GitHub 项目调研登记

核验日期：2026-07-24。方法：官方 GitHub 页面、`git ls-remote --symref`、官方 raw LICENSE；GitHub REST API 当日受共享速率限制，不能据此编造更新时间。所有项目当前仅作为研究资料，未复制源码、主题、提示词或资产，未新增为依赖。

## 微信排版与发布

| 项目 | 解决问题 / 可借鉴 | 许可证核验 | 当前状态 | 采用决定 |
|---|---|---|---|---|
| [doocs/md](https://github.com/doocs/md) | Markdown主题、微信排版、图片与编辑体验 | 当前根 LICENSE 为 WTFPL-2.0；模板/资产仍需单查 | 官方仓库可达，main | 只研究主题分层；不引入前端 |
| [jiji262/wechat-publisher](https://github.com/jiji262/wechat-publisher) | 内容→配图→HTML→图片上传→草稿 | 根目录未发现常见 LICENSE，视为权利保留 | 官方仓库可达，main | 只研究公开接口描述；不复制/依赖 |
| [geekjourneyx/md2wechat-skill](https://github.com/geekjourneyx/md2wechat-skill) | Agent CLI、结构模块、确定性主题与草稿 | Source Available/BUSL派生；2030-01-01前有商业/再分发限制 | 官方仓库可达，main | 明确不吸收代码/主题/Prompt；仅产品对照 |
| [eesast/md2wx](https://github.com/eesast/md2wx) | 简单 Markdown→微信 HTML | MIT | 官方仓库可达，master | 对照基础兼容；当前自实现更轻 |
| [Tencent/weui](https://github.com/Tencent/weui) | 微信移动视觉语言 | MIT | 官方仓库可达，master | 视觉参考；不是公众号正文组件库 |

## AI 内容编辑与审阅

| 项目 | 可借鉴能力 | 许可证核验 | 当前状态 | 采用决定 |
|---|---|---|---|---|
| [Open Canvas](https://github.com/langchain-ai/open-canvas) | 从既有文档开始、反思/记忆、多Agent文档协作 | MIT | 官方仓库可达，main | 借鉴“内容先审阅”；不引入完整应用 |
| [Tersa](https://github.com/haydenbleasel/tersa) | 可视化AI节点工作流 | 未发现常见根 LICENSE，待作者/仓库进一步确认 | 官方仓库可达，main | 只作流程图思想参考 |
| [Plate](https://github.com/udecode/plate) | 结构化富文本、AI、插件节点 | MIT | 官方仓库可达，main | 借鉴节点与审阅；不引入React编辑器 |
| [BlockNote](https://github.com/TypeCellOS/BlockNote) | 块编辑、ProseMirror/Tiptap、协作 | 核心 MPL-2.0；`xl-*` 为 GPL-3.0且有额外说明 | 官方仓库可达，main | 不成为依赖；避免XL许可证扩散风险 |
| [Yoopta Editor](https://github.com/Darginec05/Yoopta-Editor) | 块编辑、插件、HTML/Markdown导出 | MIT | 官方仓库可达，master | 只借鉴可序列化节点 |

## 视觉组件与画布

| 项目 | 可借鉴能力 | 许可证 | 当前状态 | 采用决定 |
|---|---|---|---|---|
| [Konva](https://github.com/konvajs/konva) | Canvas对象、层、序列化、导出 | MIT | 官方页面和版本活动可见 | 未来封面/复杂区块可选；当前不依赖 |
| [Fabric.js](https://github.com/fabricjs/fabric.js) | 文字/形状/图片对象、JSON/SVG导出 | MIT | 官方页面和版本活动可见 | 同上，待有画布需求再选型 |
| [GrapesJS](https://github.com/GrapesJS/grapesjs) | Block/Style/Asset Manager、Newsletter场景 | core LICENSE为BSD风格三条款 | 官方仓库可达，dev | 只借鉴管理模型；输出不能直接当微信HTML |

## 素材、图表与动效

| 项目 | 能力 | 许可证 | 当前状态 | 采用决定 |
|---|---|---|---|---|
| [Iconify API](https://github.com/iconify/api) / [icon-sets](https://github.com/iconify/icon-sets) | 图标搜索与SVG | 框架许可不等于每个集合许可 | 官方仓库可达 | 已实现API接口；仅白名单集合并逐集合登记 |
| [Apache ECharts](https://github.com/apache/echarts) | 图表配置、SVG/Canvas、SSR | Apache-2.0 | 官方仓库可达，master | 保留静态渲染接口；本机未安装真实引擎 |
| [Mermaid](https://github.com/mermaid-js/mermaid) | 文本流程图 | MIT | 官方仓库可达，develop | CLI存在时严格模式；否则程序/文字降级 |
| [Vega-Lite](https://github.com/vega/vega-lite) | 声明式图表规范 | BSD-3-Clause | 官方仓库可达，main | 保留接口与静态降级；不加载外部数据URL |
| [Lottie-web](https://github.com/airbnb/lottie-web) | 动效预览/渲染 | MIT | 官方仓库可达，master | 仅预览/首帧/GIF/视频；微信不运行JS |
| [Rive runtime](https://github.com/rive-app/rive-runtime) | 矢量动画运行与渲染 | MIT运行时；社区资产另行许可 | 官方仓库可达，main | 不依赖；社区文件逐项核验并静态降级 |

## 结论

当前版本没有必要引入大型编辑器或画布库。可复用的核心思想已经以轻量数据结构、脚本接口和 Mock 实现：节点化 Article Schema、内容锁定/版本、组件策略、静态降级、来源/许可证账本与微信幂等保护。
