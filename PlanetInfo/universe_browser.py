from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from PIL import Image
except Exception:  # pillow optional at runtime for preview export
    Image = None

MASK32 = 0xFFFFFFFF


# -------------------------------
# Hash and key logic from source
# -------------------------------
def u32(n: int) -> int:
    return n & MASK32


def csharp_int32(n: int) -> int:
    n &= MASK32
    return n if n < 0x80000000 else n - 0x100000000


def csharp_mod(a: int, b: int) -> int:
    return a - int(a / b) * b


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
        return HashUtility.hash_uint(u32(offset * width + height + i + j * width))


def slice_self_map_key_index(map_key: str) -> str:
    idx = map_key.index("#")
    return map_key[idx:]


def build_map_key(map_type: str, coords: Iterable[Tuple[int, int]]) -> str:
    suffix = "".join(f"={x},{y}" for x, y in coords)
    return f"Weathering.{map_type}#{suffix}"


# -------------------------------
# Universe model
# -------------------------------
STAR_TYPES = ["蓝色恒星", "白色恒星", "黄色恒星", "橙色恒星", "红色恒星"]

PLAYABLE_PLANET_TYPES = {
    "PlanetBarren": "荒芜行星",
    "PlanetArid": "干旱行星",
    "PlanetOcean": "海洋行星",
    "PlanetMolten": "熔岩行星",
    "PlanetFrozen": "冰冻星球",
    "PlanetContinental": "类地行星",
}

CELESTIAL_LOCALIZED = {
    "SpaceEmptiness": "虚空",
    "Asteroid": "小行星",
    "GasGiant": "气态巨行星",
    "GasGiantRinged": "环状气态巨行星",
    "PlanetGaia": "盖亚行星",
    "PlanetSuperDimensional": "超维星球",
    **PLAYABLE_PLANET_TYPES,
}


@dataclass(frozen=True)
class GalaxyRecord:
    pos: Tuple[int, int]
    map_key: str


@dataclass(frozen=True)
class StarSystemRecord:
    galaxy_pos: Tuple[int, int]
    pos: Tuple[int, int]
    map_key: str
    star_type: str
    star_positions: List[Tuple[int, int]]


@dataclass(frozen=True)
class PlanetRecord:
    galaxy_pos: Tuple[int, int]
    star_system_pos: Tuple[int, int]
    pos: Tuple[int, int]
    map_key: str
    celestial_type: str
    star_type: str
    seconds_for_a_day: int
    days_for_a_month: int
    month_for_a_year: int
    days_for_a_year: int
    planet_size: int
    mineral_density: int


def universe_tile_hash(x: int, y: int) -> int:
    # MapOfUniverse hash == Hash("Weathering.MapOfUniverse#")
    map_hash = csharp_int32(HashUtility.hash_string("Weathering.MapOfUniverse#"))
    return HashUtility.hash_tile(x, y, 100, 100, map_hash)


def galaxy_exists(x: int, y: int) -> bool:
    return universe_tile_hash(x, y) % 50 == 0


def galaxy_tile_hash(gx: int, gy: int, sx: int, sy: int) -> int:
    map_key = build_map_key("MapOfGalaxy", [(gx, gy)])
    map_hash = csharp_int32(HashUtility.hash_string(map_key))
    return HashUtility.hash_tile(sx, sy, 100, 100, map_hash)


def star_system_exists(gx: int, gy: int, sx: int, sy: int) -> bool:
    return galaxy_tile_hash(gx, gy, sx, sy) % 200 == 0


def star_system_map_key(g: Tuple[int, int], s: Tuple[int, int]) -> str:
    return build_map_key("MapOfStarSystem", [g, s])


def compute_star_positions(system_map_key: str) -> List[Tuple[int, int]]:
    # MapOfStarSystem.OnConstruct
    h = HashUtility.hash_string(system_map_key)
    star_pos = abs(csharp_int32(h) % (32 * 32))
    x1, y1 = star_pos % 32, star_pos // 32
    second = HashUtility.hash_uint(h)
    second_pos = abs(csharp_int32(second))
    if second_pos == star_pos:
        return [(x1, y1)]
    x2, y2 = second_pos % 32, second_pos // 32
    return [(x1, y1), (x2, y2)]


def compute_star_type(system_map_key: str) -> str:
    # MapOfGalaxyDefaultTile.CalculateStarType(GameEntry.ChildMapKeyHashCode(...))
    v = HashUtility.hash_string(slice_self_map_key_index(system_map_key))
    return STAR_TYPES[v % 5]


def classify_celestial(system_map_key: str, pos: Tuple[int, int]) -> str:
    stars = set(compute_star_positions(system_map_key))
    if pos in stars:
        return "Star"
    system_hash = csharp_int32(HashUtility.hash_string(system_map_key))
    tile_hash = HashUtility.hash_tile(pos[0], pos[1], 32, 32, system_hash)
    h = HashUtility.hash_uint(tile_hash)

    h, v = HashUtility.hashed_ref(h)
    if v % 50 != 0:
        return "SpaceEmptiness"
    h, v = HashUtility.hashed_ref(h)
    if v % 2 != 0:
        return "Asteroid"
    h, v = HashUtility.hashed_ref(h)
    if v % 40 == 0:
        return "PlanetGaia"
    h, v = HashUtility.hashed_ref(h)
    if v % 40 == 0:
        return "PlanetSuperDimensional"
    h, v = HashUtility.hashed_ref(h)
    if v % 10 == 0:
        return "GasGiant"
    h, v = HashUtility.hashed_ref(h)
    if v % 9 == 0:
        return "GasGiantRinged"
    h, v = HashUtility.hashed_ref(h)
    if v % 3 == 0:
        return "PlanetContinental"
    h, v = HashUtility.hashed_ref(h)
    if v % 2 == 0:
        return "PlanetMolten"
    h, v = HashUtility.hashed_ref(h)
    if v % 4 == 0:
        return "PlanetBarren"
    h, v = HashUtility.hashed_ref(h)
    if v % 3 == 0:
        return "PlanetArid"
    h, v = HashUtility.hashed_ref(h)
    if v % 2 == 0:
        return "PlanetFrozen"
    return "PlanetOcean"


def compute_planet(g: Tuple[int, int], s: Tuple[int, int], p: Tuple[int, int]) -> Optional[PlanetRecord]:
    s_key = star_system_map_key(g, s)
    celestial = classify_celestial(s_key, p)
    if celestial not in PLAYABLE_PLANET_TYPES:
        return None

    # SecondsForADay from MapOfStarSystemDefaultTile
    sh = csharp_int32(HashUtility.hash_string(s_key))
    tile_hash = HashUtility.hash_tile(p[0], p[1], 32, 32, sh)
    again = HashUtility.hash_uint(tile_hash)
    again = HashUtility.hash_uint(again)
    slowed_animation = 1 + abs(csharp_mod(csharp_int32(again), 7))
    seconds = (60 * 8) // (1 + slowed_animation)

    p_key = build_map_key("MapOfPlanet", [g, s, p])
    self_idx_hash = HashUtility.hash_string(slice_self_map_key_index(p_key))
    month_days = 2 + (HashUtility.hash_string(p_key) % 15)
    month_per_year = 12

    return PlanetRecord(
        galaxy_pos=g,
        star_system_pos=s,
        pos=p,
        map_key=p_key,
        celestial_type=PLAYABLE_PLANET_TYPES[celestial],
        star_type=compute_star_type(s_key),
        seconds_for_a_day=seconds,
        days_for_a_month=month_days,
        month_for_a_year=month_per_year,
        days_for_a_year=month_days * month_per_year,
        planet_size=50 + (self_idx_hash % 100),
        mineral_density=3 + (HashUtility.add_salt(self_idx_hash, 2641779086) % 27),
    )


def build_universe() -> Dict[str, List]:
    galaxies: List[GalaxyRecord] = []
    star_systems: List[StarSystemRecord] = []
    planets: List[PlanetRecord] = []

    for gy in range(100):
        for gx in range(100):
            if not galaxy_exists(gx, gy):
                continue
            g = (gx, gy)
            g_key = build_map_key("MapOfGalaxy", [g])
            galaxies.append(GalaxyRecord(pos=g, map_key=g_key))
            for sy in range(100):
                for sx in range(100):
                    if not star_system_exists(gx, gy, sx, sy):
                        continue
                    s = (sx, sy)
                    s_key = star_system_map_key(g, s)
                    star_systems.append(
                        StarSystemRecord(
                            galaxy_pos=g,
                            pos=s,
                            map_key=s_key,
                            star_type=compute_star_type(s_key),
                            star_positions=compute_star_positions(s_key),
                        )
                    )
                    for py in range(32):
                        for px in range(32):
                            rec = compute_planet(g, s, (px, py))
                            if rec:
                                planets.append(rec)

    return {"galaxies": galaxies, "star_systems": star_systems, "planets": planets}


def export_planet_preview(planet: PlanetRecord, out_path: Path) -> Path:
    if Image is None:
        raise RuntimeError("缺少 Pillow，无法导出预览图")

    tex_map = {
        "类地行星": "Assets/Tiles/Planets/PlanetContinental_Base.png",
        "冰冻星球": "Assets/Tiles/Planets/PlanetFrozen_Base.png",
        "荒芜行星": "Assets/Tiles/Planets/PlanetBarren_Base.png",
        "干旱行星": "Assets/Tiles/Planets/PlanetArid_Base 1.png",
        "熔岩行星": "Assets/Tiles/Planets/PlanetMolten_Base.png",
        "海洋行星": "Assets/Tiles/Planets/PlanetOcean_Base.png",
    }
    src = tex_map.get(planet.celestial_type)
    if not src or not Path(src).exists():
        raise RuntimeError(f"找不到贴图: {src}")

    img = Image.open(src).convert("RGBA")
    w, h = img.size
    frames = 64 if w >= 64 and w % 64 == 0 else 1
    fw = w // frames
    frame = img.crop((0, 0, fw, h))
    frame.save(out_path)
    return out_path


class UniverseBrowser:
    def __init__(self, data: Dict[str, List]):
        self.data = data
        self.root = tk.Tk()
        self.root.title("Weathering 宇宙信息筛选器")
        self.root.geometry("1300x780")

        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=8, pady=6)

        self.search_var = tk.StringVar()
        self.type_var = tk.StringVar(value="全部")
        self.sort_var = tk.StringVar(value="map_key")

        ttk.Label(top, text="查询:").pack(side=tk.LEFT)
        ttk.Entry(top, textvariable=self.search_var, width=34).pack(side=tk.LEFT, padx=4)
        ttk.Label(top, text="筛选:").pack(side=tk.LEFT, padx=(8, 0))
        ttk.Combobox(top, textvariable=self.type_var, values=["全部", "星系", "恒星系", "星球"], width=10, state="readonly").pack(side=tk.LEFT, padx=4)
        ttk.Label(top, text="排序字段:").pack(side=tk.LEFT)
        ttk.Combobox(top, textvariable=self.sort_var, values=["map_key", "planet_size", "mineral_density", "seconds_for_a_day"], width=18, state="readonly").pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="应用", command=self.reload_tree).pack(side=tk.LEFT, padx=6)

        pane = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=2)
        pane.add(right, weight=3)

        self.tree = ttk.Treeview(left, columns=("kind", "map_key"), show="tree headings")
        self.tree.heading("kind", text="类型")
        self.tree.heading("map_key", text="MapKey")
        self.tree.column("kind", width=90, anchor=tk.CENTER)
        self.tree.column("map_key", width=560)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.text = tk.Text(right, wrap=tk.WORD)
        self.text.pack(fill=tk.BOTH, expand=True)

        ttk.Button(right, text="导出所选星球预览", command=self.export_selected_preview).pack(anchor=tk.E, pady=(6, 0))

        self.id_to_obj: Dict[str, object] = {}
        self.reload_tree()

    def reload_tree(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.id_to_obj.clear()

        q = self.search_var.get().strip()
        only = self.type_var.get()
        sort_by = self.sort_var.get()

        galaxies: List[GalaxyRecord] = self.data["galaxies"]
        systems: List[StarSystemRecord] = self.data["star_systems"]
        planets: List[PlanetRecord] = self.data["planets"]
        if sort_by and hasattr(PlanetRecord, sort_by):
            planets = sorted(planets, key=lambda x: getattr(x, sort_by))

        by_g: Dict[Tuple[int, int], List[StarSystemRecord]] = {}
        by_s: Dict[Tuple[Tuple[int, int], Tuple[int, int]], List[PlanetRecord]] = {}
        for s in systems:
            by_g.setdefault(s.galaxy_pos, []).append(s)
        for p in planets:
            by_s.setdefault((p.galaxy_pos, p.star_system_pos), []).append(p)

        for g in galaxies:
            g_text = f"MapOfGalaxy#{g.pos[0]},{g.pos[1]}"
            if only == "星系" and q and q not in g_text and q not in g.map_key:
                continue
            gid = self.tree.insert("", tk.END, text=f"星系 {g.pos}", values=("星系", g.map_key), open=False)
            self.id_to_obj[gid] = g
            if only == "星系":
                continue
            for s in by_g.get(g.pos, []):
                s_text = f"MapOfStarSystem#{s.pos[0]},{s.pos[1]}"
                if q and q not in s_text and q not in s.map_key and q not in s.star_type:
                    pass
                sid = self.tree.insert(gid, tk.END, text=f"恒星系 {s.pos} [{s.star_type}]", values=("恒星系", s.map_key), open=False)
                self.id_to_obj[sid] = s
                if only == "恒星系":
                    continue
                for p in by_s.get((g.pos, s.pos), []):
                    if q and q not in p.map_key and q not in p.celestial_type and q not in p.star_type:
                        continue
                    pid = self.tree.insert(sid, tk.END, text=f"星球 {p.pos} [{p.celestial_type}]", values=("星球", p.map_key), open=False)
                    self.id_to_obj[pid] = p

    def on_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        obj = self.id_to_obj.get(sel[0])
        self.text.delete("1.0", tk.END)
        if obj is None:
            return
        data = asdict(obj)
        if isinstance(obj, PlanetRecord):
            data["planet_map_preview_hint"] = "可点击右侧按钮导出贴图预览(PNG)"
        self.text.insert("1.0", json.dumps(data, ensure_ascii=False, indent=2))

    def export_selected_preview(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一个星球节点")
            return
        obj = self.id_to_obj.get(sel[0])
        if not isinstance(obj, PlanetRecord):
            messagebox.showwarning("提示", "当前选择不是星球")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not path:
            return
        try:
            out = export_planet_preview(obj, Path(path))
            messagebox.showinfo("完成", f"已导出: {out}")
        except Exception as e:
            messagebox.showerror("失败", str(e))

    def run(self):
        self.root.mainloop()


# -------------------------------
# CLI
# -------------------------------
def verify_samples() -> None:
    samples = {
        "Weathering.MapOfPlanet#=1,4=14,93=24,31": {
            "seconds_for_a_day": 160,
            "days_for_a_year": 60,
            "days_for_a_month": 5,
            "month_for_a_year": 12,
            "planet_size": 142,
            "mineral_density": 5,
            "celestial_type": "类地行星",
            "star_type": "橙色恒星",
        },
        "Weathering.MapOfPlanet#=1,4=14,93=24,1": {
            "seconds_for_a_day": 80,
            "days_for_a_year": 24,
            "days_for_a_month": 2,
            "month_for_a_year": 12,
            "planet_size": 71,
            "mineral_density": 3,
            "celestial_type": "冰冻星球",
            "star_type": "橙色恒星",
        },
        "Weathering.MapOfPlanet#=97,11=18,1=20,6": {
            "seconds_for_a_day": 80,
            "days_for_a_year": 60,
            "days_for_a_month": 5,
            "month_for_a_year": 12,
            "planet_size": 120,
            "mineral_density": 7,
            "celestial_type": "荒芜行星",
            "star_type": "黄色恒星",
        },
    }

    def parse(pkey: str) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
        _, idx = pkey.split("#", 1)
        a, b, c = idx.split("=")[1:]
        def xy(z: str) -> Tuple[int, int]:
            x, y = z.split(",")
            return int(x), int(y)
        return xy(a), xy(b), xy(c)

    for pkey, expected in samples.items():
        g, s, p = parse(pkey)
        r = compute_planet(g, s, p)
        if r is None:
            raise AssertionError(f"{pkey} 未生成为可登陆星球")
        got = asdict(r)
        for k, v in expected.items():
            if got[k] != v:
                raise AssertionError(f"{pkey} {k}: got={got[k]} expected={v}")


def main():
    ap = argparse.ArgumentParser(description="Weathering 宇宙信息筛选器")
    ap.add_argument("--verify", action="store_true", help="校验给定样本坐标")
    ap.add_argument("--dump-json", type=str, help="将全部宇宙信息导出 JSON")
    ap.add_argument("--no-ui", action="store_true", help="仅生成数据，不启动 UI")
    args = ap.parse_args()

    if args.verify:
        verify_samples()
        print("样本校验通过")

    data = None
    if args.dump_json or not args.no_ui:
        data = build_universe()

    if args.dump_json:
        out = {
            "galaxies": [asdict(x) for x in data["galaxies"]],
            "star_systems": [asdict(x) for x in data["star_systems"]],
            "planets": [asdict(x) for x in data["planets"]],
        }
        Path(args.dump_json).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        print(f"已导出: {args.dump_json}")

    if not args.no_ui:
        UniverseBrowser(data).run()


if __name__ == "__main__":
    main()
