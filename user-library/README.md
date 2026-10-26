# 个人素材仓库

建议目录：`images/ videos/ documents/ components/ svg/ brand-kits/ references/ templates/ historical-articles/`。

把用户资产放入对应目录，保留原文件，不在这里存真实凭证。运行：

```powershell
python ../scripts/library.py build . --output library-index.json
python ../scripts/library.py search library-index.json "关键词"
```

自动索引默认把许可证状态设为 `unknown`。请根据 `license-register.example.csv` 补充作者、来源、商用/署名/修改/再分发权限和到期日；未确认素材不得自动发布。私人素材默认只在本地处理。
