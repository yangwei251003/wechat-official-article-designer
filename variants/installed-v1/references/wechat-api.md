# 微信草稿箱接口

## 安全边界

- 只读取环境变量 `WECHAT_APP_ID`、`WECHAT_APP_SECRET`；不要写入文章包、技能或日志。
- 默认干跑；只有用户明确要求本次创建草稿时使用 `--commit`。
- 只创建草稿，不调用发布或群发接口。
- access token只缓存在用户临时目录，日志中始终脱敏。

## 流程

1. 获取access token。
2. 将正文JPG/PNG上传到 `media/uploadimg`，用返回的微信URL替换HTML中的本地路径。
3. 将封面上传为永久图片素材，取得 `thumb_media_id`。
4. 校验正文已无本地、data和未知外链图片。
5. 调用 `draft/add` 创建草稿。
6. 把草稿ID和图片映射写入 `publish-result.json`。

## 未知状态保护

调用 `draft/add` 前写入 `publish-pending.json`。成功或明确的API错误后删除；连接超时、断线等无法判断服务端是否收到请求时保留。存在pending文件时禁止再次创建草稿。用户必须先到微信后台核对，再显式运行：

```powershell
python <skill>/scripts/publish_wechat.py <package> --clear-pending
```

## 干跑与提交

```powershell
python <skill>/scripts/publish_wechat.py <package>
python <skill>/scripts/publish_wechat.py <package> --commit
```

脚本不得输出AppSecret或完整access token。IP白名单、权限、文件限制等错误要保留 `errcode`，并给出可行动的说明。

