from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Iterable, List, Optional, Tuple

MASK32 = 0xFFFFFFFF

UNIVERSE_SIZE = 100
GALAXY_SIZE = 100
STAR_SYSTEM_SIZE = 32


# ------------------ C# compatibility helpers ------------------
def u32(n: int) -> int:
    return n & MASK32


def csharp_int32(n: int) -> int:
    n &= MASK32
    return n if n < 0x80000000 else n - 0x100000000


def csharp_mod(a: int, b: int) -> int:
    return a - int(a / b) * b


# ------------------ Port of HashUtility.cs ------------------
class HashUtility:
    @staticmethod
    def hash_uint(a: int) -> int:
        a = u32((a ^ 61) ^ (a >> 16))
        a = u32(a + (a << 3))
        a = u32(a ^ (a >> 4))
        a = u32(a * 0x27D4EB2D)
        a = u32(a ^ (a >> 15))
        return a

    @staticmethod
    def hash_string(text: str) -> int:
        result = 7
        for c in text:
            result = u32(result + ord(c))
            result = HashUtility.hash_uint(result)
        return result

    @staticmethod
    def hashed_ref(x: int) -> Tuple[int, int]:
        x = HashUtility.hash_uint(x)
        return x, x

    @staticmethod
    def add_salt(a: int, salt: int) -> int:
        return HashUtility.hash_uint(u32(a + salt))

    @staticmethod
    def hash_tile(i: int, j: int, width: int, height: int, offset: int = 0) -> int:
        raw = u32(offset * width + height + i + j * width)
        return HashUtility.hash_uint(raw)

    @staticmethod
    def random_vec2_simple(i: int, j: int, width: int, height: int, offset: int = 0) -> Tuple[float, float]:
        i %= width
        j %= height
        h = HashUtility.hash_tile(i, j, width, height, offset)
        if h % 4 == 0:
            return -1.0, 1.0
        if h % 4 == 1:
            return -1.0, -1.0
        if h % 4 == 2:
            return 1.0, 1.0
        return 1.0, -1.0

    @staticmethod
    def perlin_noise(x: float, y: float, width: int, height: int, layer: int = 0) -> float:
        p0x, p0y = int(x), int(y)
        p1x, p1y = p0x, p0y + 1
        p2x, p2y = p0x + 1, p0y + 1
        p3x, p3y = p0x + 1, p0y

        g0x, g0y = HashUtility.random_vec2_simple(p0x, p0y, width, height, layer)
        g1x, g1y = HashUtility.random_vec2_simple(p1x, p1y, width, height, layer)
        g2x, g2y = HashUtility.random_vec2_simple(p2x, p2y, width, height, layer)
        g3x, g3y = HashUtility.random_vec2_simple(p3x, p3y, width, height, layer)

        v0x, v0y = x - p0x, y - p0y
        v1x, v1y = x - p1x, y - p1y
        v2x, v2y = x - p2x, y - p2y
        v3x, v3y = x - p3x, y - p3y

        product0 = g0x * v0x + g0y * v0y
        product1 = g1x * v1x + g1y * v1y
        product2 = g2x * v2x + g2y * v2y
        product3 = g3x * v3x + g3y * v3y

        dx = x - p0x
        dy = y - p0y
        sx = dx * dx * dx * (dx * (dx * 6 - 15) + 10)
        sy = dy * dy * dy * (dy * (dy * 6 - 15) + 10)

        p01 = product0 * (1.0 - sy) + product1 * sy
        p32 = product3 * (1.0 - sy) + product2 * sy
        return p01 * (1.0 - sx) + p32 * sx


STAR_TYPES = {0: "蓝色恒星", 1: "白色恒星", 2: "黄色恒星", 3: "橙色恒星", 4: "红色恒星"}
PLANET_TYPES = {
    "PlanetBarren": "荒芜行星",
    "PlanetArid": "干旱行星",
    "PlanetOcean": "海洋行星",
    "PlanetMolten": "熔岩行星",
    "PlanetFrozen": "冰冻星球",
    "PlanetContinental": "类地行星",
    "PlanetGaia": "盖亚行星",
    "PlanetSuperDimensional": "超维星球",
}


@dataclass(frozen=True)
class GalaxyRecord:
    pos: Tuple[int, int]


@dataclass(frozen=True)
class StarSystemRecord:
    galaxy_pos: Tuple[int, int]
    pos: Tuple[int, int]
    star_type: str


@dataclass(frozen=True)
class PlanetRecord:
    map_key: str
    galaxy_pos: Tuple[int, int]
    star_system_pos: Tuple[int, int]
    planet_pos: Tuple[int, int]
    star_type: str
    planet_type: str
    seconds_for_a_day: int
    days_for_a_month: int
    days_for_a_year: int
    month_for_a_year: int
    planet_size: int
    mineral_density: int


def parse_map_key(map_key: str) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
    _, index = map_key.split("#", 1)
    coords = [p for p in index.split("=") if p]
    parsed: List[Tuple[int, int]] = []
    for c in coords:
        x, y = c.split(",")
        parsed.append((int(x), int(y)))
    if len(parsed) != 3:
        raise ValueError(map_key)
    return parsed[0], parsed[1], parsed[2]


def build_map_key(map_type: str, coords: Iterable[Tuple[int, int]]) -> str:
    suffix = "".join(f"={x},{y}" for x, y in coords)
    return f"Weathering.{map_type}#{suffix}"


def slice_self_map_key_index(map_key: str) -> str:
    return map_key[map_key.index("#"):]


def is_galaxy(universe_pos: Tuple[int, int]) -> bool:
    universe_hash = HashUtility.hash_string("Weathering.MapOfUniverse#")
    tile_hash = HashUtility.hash_tile(universe_pos[0], universe_pos[1], UNIVERSE_SIZE, UNIVERSE_SIZE, csharp_int32(universe_hash))
    return tile_hash % 50 == 0


def is_star_system(galaxy_pos: Tuple[int, int], star_pos: Tuple[int, int]) -> bool:
    galaxy_map_key = build_map_key("MapOfGalaxy", [galaxy_pos])
    galaxy_hash = HashUtility.hash_string(galaxy_map_key)
    tile_hash = HashUtility.hash_tile(star_pos[0], star_pos[1], GALAXY_SIZE, GALAXY_SIZE, csharp_int32(galaxy_hash))
    return tile_hash % 200 == 0


def calculate_star_type(star_system_map_key: str) -> str:
    star_hash = HashUtility.hash_string(slice_self_map_key_index(star_system_map_key))
    return STAR_TYPES[star_hash % 5]


def _star_positions(star_system_map_key: str) -> Tuple[Tuple[int, int], Optional[Tuple[int, int]]]:
    h = HashUtility.hash_string(star_system_map_key)
    star_pos = abs(csharp_int32(h)) % (STAR_SYSTEM_SIZE * STAR_SYSTEM_SIZE)
    main = (star_pos % STAR_SYSTEM_SIZE, star_pos // STAR_SYSTEM_SIZE)
    second_hash = HashUtility.hash_uint(h)
    second_pos = abs(csharp_int32(second_hash))
    if second_pos == star_pos:
        return main, None
    return main, (second_pos % STAR_SYSTEM_SIZE, second_pos // STAR_SYSTEM_SIZE)


def compute_planet_record(planet_map_key: str) -> PlanetRecord:
    g_pos, s_pos, p_pos = parse_map_key(planet_map_key)
    star_system_map_key = build_map_key("MapOfStarSystem", [g_pos, s_pos])
    star_system_hash = HashUtility.hash_string(star_system_map_key)
    tile_hash = HashUtility.hash_tile(p_pos[0], p_pos[1], STAR_SYSTEM_SIZE, STAR_SYSTEM_SIZE, csharp_int32(star_system_hash))

    main_star, second_star = _star_positions(star_system_map_key)
    is_star_tile = p_pos == main_star or (second_star is not None and p_pos == second_star)

    hashcode = HashUtility.hash_uint(tile_hash)
    if is_star_tile:
        celestial = "Star"
    else:
        hashcode, v = HashUtility.hashed_ref(hashcode)
        if v % 50 != 0:
            celestial = "SpaceEmptiness"
        else:
            hashcode, v = HashUtility.hashed_ref(hashcode)
            if v % 2 != 0:
                celestial = "Asteroid"
            else:
                hashcode, v = HashUtility.hashed_ref(hashcode)
                if v % 40 == 0:
                    celestial = "PlanetGaia"
                else:
                    hashcode, v = HashUtility.hashed_ref(hashcode)
                    if v % 40 == 0:
                        celestial = "PlanetSuperDimensional"
                    else:
                        hashcode, v = HashUtility.hashed_ref(hashcode)
                        if v % 10 == 0:
                            celestial = "GasGiant"
                        else:
                            hashcode, v = HashUtility.hashed_ref(hashcode)
                            if v % 9 == 0:
                                celestial = "GasGiantRinged"
                            else:
                                hashcode, v = HashUtility.hashed_ref(hashcode)
                                if v % 3 == 0:
                                    celestial = "PlanetContinental"
                                else:
                                    hashcode, v = HashUtility.hashed_ref(hashcode)
                                    if v % 2 == 0:
                                        celestial = "PlanetMolten"
                                    else:
                                        hashcode, v = HashUtility.hashed_ref(hashcode)
                                        if v % 4 == 0:
                                            celestial = "PlanetBarren"
                                        else:
                                            hashcode, v = HashUtility.hashed_ref(hashcode)
                                            if v % 3 == 0:
                                                celestial = "PlanetArid"
                                            else:
                                                hashcode, v = HashUtility.hashed_ref(hashcode)
                                                celestial = "PlanetFrozen" if v % 2 == 0 else "PlanetOcean"

    if celestial not in PLANET_TYPES:
        raise ValueError(f"not playable planet: {celestial}")

    again = HashUtility.hash_uint(tile_hash)
    again = HashUtility.hash_uint(again)
    slowed_animation = 1 + abs(csharp_mod(csharp_int32(again), 7))
    seconds_for_a_day = (60 * 8) // (1 + slowed_animation)

    planet_hash = HashUtility.hash_string(planet_map_key)
    self_hash = HashUtility.hash_string(slice_self_map_key_index(planet_map_key))
    days_for_a_month = 2 + (planet_hash % 15)
    month_for_a_year = 12
    days_for_a_year = month_for_a_year * days_for_a_month
    planet_size = 50 + (self_hash % 100)
    mineral_density = 3 + (HashUtility.add_salt(self_hash, 2641779086) % 27)

    return PlanetRecord(
        map_key=planet_map_key,
        galaxy_pos=g_pos,
        star_system_pos=s_pos,
        planet_pos=p_pos,
        star_type=calculate_star_type(star_system_map_key),
        planet_type=PLANET_TYPES[celestial],
        seconds_for_a_day=seconds_for_a_day,
        days_for_a_month=days_for_a_month,
        days_for_a_year=days_for_a_year,
        month_for_a_year=month_for_a_year,
        planet_size=planet_size,
        mineral_density=mineral_density,
    )


def planet_surface_preview(record: PlanetRecord, out_path: Path) -> Path:
    size = record.planet_size
    map_hash = HashUtility.hash_string(record.map_key)
    base_alt = 5 + (map_hash % 11)
    base_moi = 7 + (map_hash % 17)

    rgb = bytearray()
    for y in range(size):
        for x in range(size):
            n0 = HashUtility.perlin_noise(base_alt * x / size, base_alt * y / size, base_alt, base_alt, 5 + csharp_int32(map_hash))
            n1 = HashUtility.perlin_noise((base_alt * 2) * x / size, (base_alt * 2) * y / size, base_alt * 2, base_alt * 2, 6 + csharp_int32(map_hash))
            n2 = HashUtility.perlin_noise((base_alt * 4) * x / size, (base_alt * 4) * y / size, base_alt * 4, base_alt * 4, 7 + csharp_int32(map_hash))
            altitude = int(-10000 + ((n0 * 4 + n1 * 2 + n2 + 7) / 14) * 19500)

            moisture = int(((HashUtility.perlin_noise(base_moi * x / size, base_moi * y / size, base_moi, base_moi, 8 + csharp_int32(map_hash)) + 1) / 2) * 100)
            temp_noise = (HashUtility.perlin_noise(4 * x / size, 4 * y / size, 4, 4, 9 + csharp_int32(map_hash)) + 1) / 2
            latitude = math.sin(math.pi * y / size)
            temp = -20 + int(((temp_noise * 0 + latitude * 1)) * 60)

            if altitude <= 0:
                color = (20, 90, 180)  # 对应 *_WaterSurface
            elif temp > 0 and moisture > 55:
                color = (30, 120, 60)  # 对应 *_Tree / *_Grass
            elif temp <= 0:
                color = (140, 140, 140)  # 对应 *_Hill
            else:
                color = (110, 170, 70)  # 对应 *_Grass
            rgb.extend(color)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as f:
        f.write(f"P6\n{size} {size}\n255\n".encode("ascii"))
        f.write(rgb)
    return out_path


class UniverseBrowser(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Weathering 宇宙信息筛选器")
        self.geometry("1300x760")

        self.details = tk.Text(self, wrap="word", width=60)
        self.search_var = tk.StringVar()
        self.sort_var = tk.StringVar(value="planet_size")
        self.filter_var = tk.StringVar(value="全部")
        self.current_planet: Optional[PlanetRecord] = None

        self._build_ui()
        self._populate_tree()
        self.tree.bind("<<TreeviewOpen>>", self._on_open)

    def _build_ui(self) -> None:
        root = ttk.PanedWindow(self, orient="horizontal")
        root.pack(fill="both", expand=True)

        left = ttk.Frame(root)
        right = ttk.Frame(root)
        root.add(left, weight=2)
        root.add(right, weight=3)

        self.tree = ttk.Treeview(left)
        self.tree.pack(fill="both", expand=True, side="left")
        yscroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        yscroll.pack(fill="y", side="right")
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        top = ttk.Frame(right)
        top.pack(fill="x")
        ttk.Label(top, text="查询").pack(side="left")
        ttk.Entry(top, textvariable=self.search_var, width=24).pack(side="left", padx=4)
        ttk.Button(top, text="执行", command=self._refresh_results).pack(side="left")
        ttk.Label(top, text="排序").pack(side="left", padx=(16, 0))
        ttk.Combobox(top, textvariable=self.sort_var, values=["planet_size", "mineral_density", "seconds_for_a_day", "days_for_a_year"], width=16).pack(side="left", padx=4)
        ttk.Label(top, text="过滤").pack(side="left", padx=(16, 0))
        ttk.Combobox(top, textvariable=self.filter_var, values=["全部", *PLANET_TYPES.values()], width=16).pack(side="left", padx=4)
        ttk.Button(top, text="导出星球地图预览", command=self._export_preview).pack(side="right")

        self.result = ttk.Treeview(right, columns=("k", "v"), show="headings", height=12)
        self.result.heading("k", text="MapKey")
        self.result.heading("v", text="类型 / 属性")
        self.result.column("k", width=420)
        self.result.column("v", width=300)
        self.result.pack(fill="x", pady=8)

        self.details.pack(fill="both", expand=True)

    def _populate_tree(self) -> None:
        uni = self.tree.insert("", "end", text="宇宙 Weathering.MapOfUniverse#", open=True, values=("universe",))
        for gy in range(UNIVERSE_SIZE):
            for gx in range(UNIVERSE_SIZE):
                if not is_galaxy((gx, gy)):
                    continue
                gnode = self.tree.insert(uni, "end", text=f"星系 {gx},{gy}", values=("galaxy", f"{gx},{gy}"))
                self.tree.insert(gnode, "end", text="...", values=("placeholder",))

    def _on_open(self, _evt: object) -> None:
        sel = self.tree.focus()
        if not sel:
            return
        vals = self.tree.item(sel, "values")
        children = self.tree.get_children(sel)
        if children and self.tree.item(children[0], "values") == ("placeholder",):
            self.tree.delete(children[0])
            if vals and vals[0] == "galaxy":
                gx, gy = map(int, vals[1].split(","))
                for sy in range(GALAXY_SIZE):
                    for sx in range(GALAXY_SIZE):
                        if not is_star_system((gx, gy), (sx, sy)):
                            continue
                        snode = self.tree.insert(sel, "end", text=f"恒星系 {sx},{sy}", values=("system", f"{gx},{gy}", f"{sx},{sy}"))
                        self.tree.insert(snode, "end", text="...", values=("placeholder",))
            elif vals and vals[0] == "system":
                gx, gy = map(int, vals[1].split(","))
                sx, sy = map(int, vals[2].split(","))
                for py in range(STAR_SYSTEM_SIZE):
                    for px in range(STAR_SYSTEM_SIZE):
                        key = build_map_key("MapOfPlanet", [(gx, gy), (sx, sy), (px, py)])
                        try:
                            p = compute_planet_record(key)
                        except ValueError:
                            continue
                        self.tree.insert(sel, "end", text=f"星球 {px},{py} {p.planet_type}", values=("planet", key))

    def _on_select(self, _evt: object) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        self.current_planet = None

        if vals and vals[0] == "planet":
            record = compute_planet_record(vals[1])
            self.current_planet = record
            self.details.delete("1.0", "end")
            self.details.insert("end", f"MapKey: {record.map_key}\n")
            self.details.insert("end", f"行星类型: {record.planet_type}\n恒星类型: {record.star_type}\n")
            self.details.insert("end", f"昼夜周期: {record.seconds_for_a_day}s\n")
            self.details.insert("end", f"四季周期: {record.days_for_a_year}天\n")
            self.details.insert("end", f"月相周期: {record.days_for_a_month}天\n")
            self.details.insert("end", f"四季月相: {record.month_for_a_year}月\n")
            self.details.insert("end", f"星球大小: {record.planet_size}\n")
            self.details.insert("end", f"矿物稀疏度: {record.mineral_density}\n")
        self._refresh_results()

    def _refresh_results(self) -> None:
        for row in self.result.get_children():
            self.result.delete(row)
        query = self.search_var.get().strip()
        planet_filter = self.filter_var.get()
        rows: List[PlanetRecord] = []

        for item in self.tree.get_children(""):
            rows.extend(self._collect_planets(item))

        if query:
            rows = [r for r in rows if query in r.map_key or query in r.planet_type or query in r.star_type]
        if planet_filter != "全部":
            rows = [r for r in rows if r.planet_type == planet_filter]
        rows.sort(key=lambda r: getattr(r, self.sort_var.get()), reverse=True)

        for r in rows[:1500]:
            self.result.insert("", "end", values=(r.map_key, f"{r.planet_type} / {r.star_type} / size={r.planet_size}"))

    def _collect_planets(self, node: str) -> List[PlanetRecord]:
        out: List[PlanetRecord] = []
        vals = self.tree.item(node, "values")
        if vals and vals[0] == "planet":
            out.append(compute_planet_record(vals[1]))
        for ch in self.tree.get_children(node):
            out.extend(self._collect_planets(ch))
        return out

    def _export_preview(self) -> None:
        if self.current_planet is None:
            messagebox.showwarning("提示", "请先选择一个星球")
            return
        path = Path("PlanetInfo/previews") / f"{self.current_planet.galaxy_pos[0]}_{self.current_planet.galaxy_pos[1]}__{self.current_planet.star_system_pos[0]}_{self.current_planet.star_system_pos[1]}__{self.current_planet.planet_pos[0]}_{self.current_planet.planet_pos[1]}.ppm"
        planet_surface_preview(self.current_planet, path)
        messagebox.showinfo("完成", f"已导出: {path}")


def _verify_samples() -> None:
    samples = {
        "Weathering.MapOfPlanet#=1,4=14,93=24,31": (160, 60, 5, 12, 142, 5, "类地行星", "橙色恒星"),
        "Weathering.MapOfPlanet#=1,4=14,93=24,1": (80, 24, 2, 12, 71, 3, "冰冻星球", "橙色恒星"),
        "Weathering.MapOfPlanet#=97,11=18,1=20,6": (80, 60, 5, 12, 120, 7, "荒芜行星", "黄色恒星"),
    }
    for k, exp in samples.items():
        r = compute_planet_record(k)
        got = (r.seconds_for_a_day, r.days_for_a_year, r.days_for_a_month, r.month_for_a_year, r.planet_size, r.mineral_density, r.planet_type, r.star_type)
        if got != exp:
            raise AssertionError(f"mismatch for {k}: got={got}, exp={exp}")


if __name__ == "__main__":
    _verify_samples()
    import os
    if os.environ.get("DISPLAY"):
        app = UniverseBrowser()
        app.mainloop()
    else:
        print("验证通过（无图形界面环境，跳过UI启动）")
