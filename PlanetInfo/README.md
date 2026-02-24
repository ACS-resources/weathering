# PlanetInfo

基于项目源码（`MapOfUniverse` / `MapOfGalaxyDefaultTile` / `MapOfStarSystem` / `MapOfStarSystemDefaultTile` / `MapOfPlanet` / `GameEntry` / `HashUtility`）复刻的宇宙检索与筛选工具。

## 能力

- 完整复刻宇宙树结构：`宇宙 -> 银河系 -> 恒星系 -> 星球`。
- 复刻原始生成逻辑：恒星系刷新、恒星颜色、天体类型、可登陆星球属性。
- 支持星球信息查询、筛选、排序。
- 支持按所选星球类型导出地图预览（使用 `Assets/Tiles/CelestialBodies/*.png` 原贴图）。

## 运行

```bash
python3 PlanetInfo/planet_explorer_ui.py
```

界面布局与注册表编辑器相似：

- 左侧：树状层级（可折叠）。
- 右侧：当前选择层级的数据表、筛选排序、详情、导出按钮。

## 验证示例

```bash
python3 PlanetInfo/planet_info.py
```

会输出示例坐标的结果，可用于和游戏内星球属性核对。
