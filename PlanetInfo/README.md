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
