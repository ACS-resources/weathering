# PlanetInfo

基于项目源码（`MapOfGalaxyDefaultTile` / `MapOfStarSystemDefaultTile` / `MapOfPlanet` / `GameEntry` / `HashUtility`）复刻的宇宙检索逻辑。

## 功能

- 解析 `Weathering.MapOfPlanet#=...` 地图坐标。
- 按游戏原逻辑计算：
  - 恒星颜色
  - 行星类型
  - 昼夜周期
  - 四季周期（年）
  - 月相周期（月）
  - 年内月相数量（固定 12）
  - 行星大小
  - 矿物稀疏度
- 支持同一恒星系内行星扫描和排序（`planets_in_star_system` / `sort_planets`）。

## 使用

```bash
python3 PlanetInfo/planet_info.py
```

会打印三个示例行星的信息（按行星大小排序）。

## 作为模块使用

```python
from PlanetInfo.planet_info import compute_planet_record, planets_in_star_system, sort_planets

r = compute_planet_record("Weathering.MapOfPlanet#=1,4=14,93=24,31")
print(r)

all_planets = planets_in_star_system((1, 4), (14, 93))
ranked = sort_planets(all_planets, by="mineral_density", reverse=True)
```

## 扩展开发手册（草案）

- 见 `PlanetInfo/AddonModDevelopmentManual.md`（中文版）。该文档基于当前 Unity 项目结构调研，提出面向 addon/mod 的标准化方案与迁移路径。

## 跨语言迁移评估

- 见 `PlanetInfo/跨语言迁移评估手册.md`。该文档评估了在忽略 Shader 等不影响核心流程的 QoL 表现后，迁移到 Python/Java 的可行性与实施路线。

## Java 迁移核心逻辑逐文件文档

- 目录：`PlanetInfo/Java迁移核心逻辑文档/`
- 索引：`PlanetInfo/Java迁移核心逻辑文档/INDEX.md`
- 说明：对核心逻辑相关 C# 文件进行一一映射，生成同名 Markdown 文档（API/dev docs 级别），用于后续逐文件 Java 原型实现与对拍测试。
