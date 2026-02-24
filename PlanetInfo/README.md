# Weathering 宇宙信息筛选器（Python）

该工具严格按仓库内 C# 源码复刻宇宙生成逻辑，生成完整树状结构：

- 宇宙 -> 星系（MapOfGalaxy）
- 星系 -> 恒星系（MapOfStarSystem）
- 恒星系 -> 星球（MapOfPlanet，可登陆行星）

并提供类似“注册表编辑器”的左右双栏 UI：

- 左栏：可折叠的父子层级树（星系 / 恒星系 / 星球）
- 右栏：当前节点详细信息（可查询、筛选、排序）
- 支持导出选中星球的贴图预览（使用游戏资源目录中的行星 Base 贴图）

## 运行

```bash
python3 PlanetInfo/universe_browser.py --verify
```

- `--verify`：校验题目给定的三个坐标是否与游戏属性一致。
- `--no-ui`：仅构建数据，不启动窗口。
- `--dump-json <path>`：导出完整宇宙数据。

例如：

```bash
python3 PlanetInfo/universe_browser.py --verify --no-ui --dump-json PlanetInfo/universe.json
```

## 说明

- 本工具不修改游戏工程代码，独立放在 `PlanetInfo/` 下。
- UI 使用 `tkinter`，预览导出需要 `Pillow`（仅导出功能依赖）。
