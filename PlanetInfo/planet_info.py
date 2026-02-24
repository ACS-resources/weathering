from __future__ import annotations

import math
import os
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Iterable, List, Optional, Tuple

MASK32 = 0xFFFFFFFF
UNIVERSE_SIZE = 100
GALAXY_SIZE = 100
STAR_SYSTEM_SIZE = 32
MONTH_FOR_A_YEAR = 12


# ========================= C# compatibility =========================
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
DISPLAY_TO_CODE = {v: k for k, v in PLANET_TYPES.items()}


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
    return f"Weathering.{map_type}#" + "".join(f"={x},{y}" for x, y in coords)


def slice_self_map_key_index(map_key: str) -> str:
    return map_key[map_key.index("#"):]


def is_galaxy(universe_pos: Tuple[int, int]) -> bool:
    universe_hash = HashUtility.hash_string("Weathering.MapOfUniverse#")
    tile_hash = HashUtility.hash_tile(universe_pos[0], universe_pos[1], UNIVERSE_SIZE, UNIVERSE_SIZE, csharp_int32(universe_hash))
    return tile_hash % 50 == 0


def is_star_system(galaxy_pos: Tuple[int, int], star_pos: Tuple[int, int]) -> bool:
    galaxy_hash = HashUtility.hash_string(build_map_key("MapOfGalaxy", [galaxy_pos]))
    tile_hash = HashUtility.hash_tile(star_pos[0], star_pos[1], GALAXY_SIZE, GALAXY_SIZE, csharp_int32(galaxy_hash))
    return tile_hash % 200 == 0


def calculate_star_type(star_system_map_key: str) -> str:
    star_hash = HashUtility.hash_string(slice_self_map_key_index(star_system_map_key))
    return STAR_TYPES[star_hash % 5]


def _star_positions(star_system_map_key: str) -> Tuple[Tuple[int, int], Optional[Tuple[int, int]]]:
    h = HashUtility.hash_string(star_system_map_key)
    star_pos = abs(csharp_int32(h)) % (STAR_SYSTEM_SIZE * STAR_SYSTEM_SIZE)
    main = (star_pos % STAR_SYSTEM_SIZE, star_pos // STAR_SYSTEM_SIZE)
    second = abs(csharp_int32(HashUtility.hash_uint(h)))
    if second == star_pos:
        return main, None
    return main, (second % STAR_SYSTEM_SIZE, second // STAR_SYSTEM_SIZE)


def _planet_base_fields(planet_map_key: str) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], str, int]:
    g_pos, s_pos, p_pos = parse_map_key(planet_map_key)
    ss_map_key = build_map_key("MapOfStarSystem", [g_pos, s_pos])
    ss_hash = HashUtility.hash_string(ss_map_key)
    tile_hash = HashUtility.hash_tile(p_pos[0], p_pos[1], STAR_SYSTEM_SIZE, STAR_SYSTEM_SIZE, csharp_int32(ss_hash))
    return g_pos, s_pos, p_pos, ss_map_key, tile_hash


def compute_planet_record(planet_map_key: str) -> PlanetRecord:
    g_pos, s_pos, p_pos, star_system_map_key, tile_hash = _planet_base_fields(planet_map_key)

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
        raise ValueError("not playable terrestrial planet")

    again = HashUtility.hash_uint(HashUtility.hash_uint(tile_hash))
    slowed = 1 + abs(csharp_mod(csharp_int32(again), 7))

    planet_hash = HashUtility.hash_string(planet_map_key)
    self_hash = HashUtility.hash_string(slice_self_map_key_index(planet_map_key))
    days_per_month = 2 + (planet_hash % 15)

    return PlanetRecord(
        map_key=planet_map_key,
        galaxy_pos=g_pos,
        star_system_pos=s_pos,
        planet_pos=p_pos,
        star_type=calculate_star_type(star_system_map_key),
        planet_type=PLANET_TYPES[celestial],
        seconds_for_a_day=(60 * 8) // (1 + slowed),
        days_for_a_month=days_per_month,
        days_for_a_year=MONTH_FOR_A_YEAR * days_per_month,
        month_for_a_year=MONTH_FOR_A_YEAR,
        planet_size=50 + (self_hash % 100),
        mineral_density=3 + (HashUtility.add_salt(self_hash, 2641779086) % 27),
    )


# ========================= map preview export =========================
def _terrain_at(record: PlanetRecord, x: int, y: int) -> str:
    size = record.planet_size
    map_hash = HashUtility.hash_string(record.map_key)
    base_alt = 5 + (map_hash % 11)
    base_moi = 7 + (map_hash % 17)

    offset_alt0 = 5 + csharp_int32(map_hash)
    offset_alt1 = 6 + csharp_int32(map_hash)
    offset_alt2 = 7 + csharp_int32(map_hash)
    offset_moi = 8 + csharp_int32(map_hash)
    offset_tmp = 9 + csharp_int32(map_hash)

    n0 = HashUtility.perlin_noise(base_alt * x / size, base_alt * y / size, base_alt, base_alt, offset_alt0)
    n1 = HashUtility.perlin_noise((base_alt * 2) * x / size, (base_alt * 2) * y / size, base_alt * 2, base_alt * 2, offset_alt1)
    n2 = HashUtility.perlin_noise((base_alt * 4) * x / size, (base_alt * 4) * y / size, base_alt * 4, base_alt * 4, offset_alt2)
    altitude = int(-10000 + ((n0 * 4 + n1 * 2 + n2 + 7) / 14) * 19500)

    moisture_noise = HashUtility.perlin_noise(base_moi * x / size, base_moi * y / size, base_moi, base_moi, offset_moi)
    moisture = int(((moisture_noise + 1) / 2) * 100)

    temp_noise = (HashUtility.perlin_noise(4 * x / size, 4 * y / size, 4, 4, offset_tmp) + 1) / 2
    latitude = math.sin(math.pi * y / size)
    temp = -20 + int((latitude) * 60) if temp_noise >= 0 else -20

    if altitude <= 0:
        return "water"
    if temp > 0:
        if moisture > 55:
            return "forest"
        return "plain"
    return "mountain"


def _asset_group_for_planet(record: PlanetRecord) -> str:
    return DISPLAY_TO_CODE[record.planet_type].replace("Planet", "")


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _load_png_rgba(path: Path) -> Tuple[int, int, bytearray]:
    raw = path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"非PNG文件: {path}")

    i = 8
    width = height = 0
    bit_depth = color_type = interlace = -1
    idat = bytearray()
    while i < len(raw):
        length = struct.unpack(">I", raw[i : i + 4])[0]
        ctype = raw[i + 4 : i + 8]
        data = raw[i + 8 : i + 8 + length]
        i += 12 + length
        if ctype == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", data)
        elif ctype == b"IDAT":
            idat.extend(data)
        elif ctype == b"IEND":
            break

    if interlace != 0:
        raise ValueError(f"不支持隔行PNG: {path}")
    if bit_depth != 8 or color_type not in (2, 6):
        raise ValueError(f"仅支持8位RGB/RGBA PNG: {path}")

    bpp = 4 if color_type == 6 else 3
    decomp = zlib.decompress(bytes(idat))
    stride = width * bpp
    out = bytearray(width * height * 4)
    prev = bytearray(stride)
    p = 0
    o = 0
    for _ in range(height):
        f = decomp[p]
        p += 1
        row = bytearray(decomp[p : p + stride])
        p += stride
        for x in range(stride):
            left = row[x - bpp] if x >= bpp else 0
            up = prev[x]
            up_left = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                row[x] = (row[x] + left) & 0xFF
            elif f == 2:
                row[x] = (row[x] + up) & 0xFF
            elif f == 3:
                row[x] = (row[x] + ((left + up) >> 1)) & 0xFF
            elif f == 4:
                row[x] = (row[x] + _paeth(left, up, up_left)) & 0xFF
        if bpp == 4:
            out[o : o + width * 4] = row
        else:
            for x in range(width):
                out[o + x * 4 + 0] = row[x * 3 + 0]
                out[o + x * 4 + 1] = row[x * 3 + 1]
                out[o + x * 4 + 2] = row[x * 3 + 2]
                out[o + x * 4 + 3] = 255
        prev = row
        o += width * 4
    return width, height, out


def _resize_nearest_rgba(width: int, height: int, rgba: bytearray, out_w: int, out_h: int) -> bytearray:
    out = bytearray(out_w * out_h * 4)
    for y in range(out_h):
        sy = int(y * height / out_h)
        for x in range(out_w):
            sx = int(x * width / out_w)
            si = (sy * width + sx) * 4
            oi = (y * out_w + x) * 4
            out[oi : oi + 4] = rgba[si : si + 4]
    return out


def _write_png_rgba(path: Path, width: int, height: int, rgba: bytearray) -> None:
    scan = bytearray()
    row = width * 4
    for y in range(height):
        scan.append(0)
        scan.extend(rgba[y * row : (y + 1) * row])
    comp = zlib.compress(bytes(scan), 9)

    def chunk(name: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
    png.extend(chunk(b"IDAT", comp))
    png.extend(chunk(b"IEND", b""))
    path.write_bytes(bytes(png))


def export_planet_preview(record: PlanetRecord, out_path: Path, tile_px: int = 24, quality: int = 95) -> Path:

    root = Path(__file__).resolve().parents[1]
    group = _asset_group_for_planet(record)
    base_dir = root / "Assets" / "Tiles" / "Planets" / group

    texture_files = {
        "plain": base_dir / f"Planet{group}_Grass.png",
        "forest": base_dir / f"Planet{group}_Tree.png",
        "water": base_dir / f"Planet{group}_WaterSurface.png",
        "mountain": base_dir / f"Planet{group}_Hill.png",
    }

    textures: Dict[str, Tuple[int, int, bytearray]] = {}
    for key, f in texture_files.items():
        if not f.exists():
            raise FileNotFoundError(f"缺少贴图: {f}")
        w, h, rgba = _load_png_rgba(f)
        textures[key] = (tile_px, tile_px, _resize_nearest_rgba(w, h, rgba, tile_px, tile_px))

    size = record.planet_size
    out_w = size * tile_px
    out_h = size * tile_px
    canvas = bytearray(out_w * out_h * 4)
    for y in range(size):
        for x in range(size):
            terrain = _terrain_at(record, x, y)
            tw, th, tile = textures[terrain]
            ox = x * tile_px
            oy = y * tile_px
            for yy in range(th):
                for xx in range(tw):
                    si = (yy * tw + xx) * 4
                    a = tile[si + 3]
                    if a == 0:
                        continue
                    di = ((oy + yy) * out_w + (ox + xx)) * 4
                    canvas[di : di + 4] = tile[si : si + 4]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ext = out_path.suffix.lower()
    if ext in {".jpg", ".jpeg"}:
        raise RuntimeError("当前环境不支持JPEG编码，请导出PNG")
    else:
        if ext != ".png":
            out_path = out_path.with_suffix(".png")
        _write_png_rgba(out_path, out_w, out_h, canvas)
    return out_path


# ========================= UI =========================
class UniverseBrowser(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Weathering 宇宙信息筛选器")
        self.geometry("1440x860")
        self.minsize(1200, 720)

        self.search_var = tk.StringVar()
        self.sort_var = tk.StringVar(value="planet_size")
        self.filter_var = tk.StringVar(value="全部")
        self.preview_scale_var = tk.StringVar(value="24")
        self.status_var = tk.StringVar(value="就绪")

        self.current_planet: Optional[PlanetRecord] = None
        self.planets_cache: Dict[str, PlanetRecord] = {}

        self._configure_style()
        self._build_ui()
        self._populate_tree()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#0f172a")
        style.configure("TLabel", background="#0f172a", foreground="#e2e8f0", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"), foreground="#93c5fd")
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TEntry", fieldbackground="#111827", foreground="#e5e7eb")
        style.configure("TCombobox", fieldbackground="#111827", foreground="#e5e7eb")
        style.configure("Treeview", background="#111827", fieldbackground="#111827", foreground="#e5e7eb", rowheight=24)
        style.configure("Treeview.Heading", background="#1f2937", foreground="#e5e7eb", font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=8)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Weathering 宇宙索引（源码一致生成）", style="Header.TLabel").pack(anchor="w", pady=(0, 8))

        panes = ttk.PanedWindow(container, orient="horizontal")
        panes.pack(fill="both", expand=True)

        left = ttk.Frame(panes)
        right = ttk.Frame(panes)
        panes.add(left, weight=2)
        panes.add(right, weight=3)

        self.tree = ttk.Treeview(left)
        y1 = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y1.set)
        self.tree.pack(side="left", fill="both", expand=True)
        y1.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewOpen>>", self._on_open)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        tools = ttk.Frame(right)
        tools.pack(fill="x", pady=(0, 8))
        ttk.Label(tools, text="查询").pack(side="left")
        ttk.Entry(tools, textvariable=self.search_var, width=24).pack(side="left", padx=4)
        ttk.Label(tools, text="类型").pack(side="left", padx=(12, 0))
        ttk.Combobox(tools, textvariable=self.filter_var, values=["全部", *PLANET_TYPES.values()], width=14, state="readonly").pack(side="left", padx=4)
        ttk.Label(tools, text="排序").pack(side="left", padx=(12, 0))
        ttk.Combobox(
            tools,
            textvariable=self.sort_var,
            values=["planet_size", "mineral_density", "seconds_for_a_day", "days_for_a_year"],
            width=16,
            state="readonly",
        ).pack(side="left", padx=4)
        ttk.Button(tools, text="应用筛选", command=self._refresh_results).pack(side="left", padx=8)

        ttk.Label(tools, text="导出格子像素").pack(side="left", padx=(12, 0))
        ttk.Combobox(tools, textvariable=self.preview_scale_var, values=["16", "24", "32", "48"], width=5, state="readonly").pack(side="left", padx=4)
        ttk.Button(tools, text="导出高清 PNG/JPEG", command=self._export_preview).pack(side="right")

        self.result = ttk.Treeview(right, columns=("k", "v"), show="headings", height=12)
        self.result.heading("k", text="MapKey")
        self.result.heading("v", text="行星 / 恒星 / 关键属性")
        self.result.column("k", width=500)
        self.result.column("v", width=420)
        self.result.pack(fill="x", pady=(0, 8))

        self.details = tk.Text(right, wrap="word", bg="#0b1220", fg="#e2e8f0", insertbackground="#e2e8f0", relief="flat", font=("Consolas", 11))
        self.details.pack(fill="both", expand=True)

        ttk.Label(container, textvariable=self.status_var).pack(anchor="w", pady=(8, 0))

    def _populate_tree(self) -> None:
        root = self.tree.insert("", "end", text="宇宙 Weathering.MapOfUniverse#", open=True, values=("universe",))
        count = 0
        for gy in range(UNIVERSE_SIZE):
            for gx in range(UNIVERSE_SIZE):
                if is_galaxy((gx, gy)):
                    g = self.tree.insert(root, "end", text=f"星系 {gx},{gy}", values=("galaxy", f"{gx},{gy}"))
                    self.tree.insert(g, "end", text="加载中...", values=("placeholder",))
                    count += 1
        self.status_var.set(f"已加载星系节点：{count}")

    def _on_open(self, _evt: object) -> None:
        node = self.tree.focus()
        if not node:
            return
        children = self.tree.get_children(node)
        if not children:
            return
        if self.tree.item(children[0], "values") != ("placeholder",):
            return

        self.tree.delete(children[0])
        vals = self.tree.item(node, "values")
        if vals[0] == "galaxy":
            gx, gy = map(int, vals[1].split(","))
            created = 0
            for sy in range(GALAXY_SIZE):
                for sx in range(GALAXY_SIZE):
                    if is_star_system((gx, gy), (sx, sy)):
                        sn = self.tree.insert(node, "end", text=f"恒星系 {sx},{sy}", values=("system", f"{gx},{gy}", f"{sx},{sy}"))
                        self.tree.insert(sn, "end", text="加载中...", values=("placeholder",))
                        created += 1
            self.status_var.set(f"星系 {gx},{gy} 已展开，恒星系数量：{created}")
        elif vals[0] == "system":
            gx, gy = map(int, vals[1].split(","))
            sx, sy = map(int, vals[2].split(","))
            created = 0
            for py in range(STAR_SYSTEM_SIZE):
                for px in range(STAR_SYSTEM_SIZE):
                    key = build_map_key("MapOfPlanet", [(gx, gy), (sx, sy), (px, py)])
                    try:
                        r = compute_planet_record(key)
                    except ValueError:
                        continue
                    self.planets_cache[key] = r
                    self.tree.insert(node, "end", text=f"星球 {px},{py} {r.planet_type}", values=("planet", key))
                    created += 1
            self.status_var.set(f"恒星系 {sx},{sy} 已展开，可登陆行星数量：{created}")

    def _on_select(self, _evt: object) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        vals = self.tree.item(selected[0], "values")
        if not vals or vals[0] != "planet":
            self.current_planet = None
            return

        key = vals[1]
        r = self.planets_cache.get(key) or compute_planet_record(key)
        self.planets_cache[key] = r
        self.current_planet = r

        self.details.delete("1.0", "end")
        self.details.insert("end", f"MapKey        : {r.map_key}\n")
        self.details.insert("end", f"坐标          : Galaxy={r.galaxy_pos}  StarSystem={r.star_system_pos}  Planet={r.planet_pos}\n")
        self.details.insert("end", f"恒星类型      : {r.star_type}\n")
        self.details.insert("end", f"行星类型      : {r.planet_type}\n")
        self.details.insert("end", f"昼夜周期      : {r.seconds_for_a_day} 秒\n")
        self.details.insert("end", f"四季周期      : {r.days_for_a_year} 天\n")
        self.details.insert("end", f"月相周期      : {r.days_for_a_month} 天\n")
        self.details.insert("end", f"四季月相      : {r.month_for_a_year} 月\n")
        self.details.insert("end", f"星球大小      : {r.planet_size}\n")
        self.details.insert("end", f"矿物稀疏度    : {r.mineral_density}\n")

        self._refresh_results()

    def _iter_loaded_planets(self) -> List[PlanetRecord]:
        return list(self.planets_cache.values())

    def _refresh_results(self) -> None:
        for row in self.result.get_children():
            self.result.delete(row)

        query = self.search_var.get().strip()
        f = self.filter_var.get()
        data = self._iter_loaded_planets()

        if query:
            data = [x for x in data if query in x.map_key or query in x.planet_type or query in x.star_type]
        if f != "全部":
            data = [x for x in data if x.planet_type == f]

        data.sort(key=lambda x: getattr(x, self.sort_var.get()), reverse=True)
        for r in data[:3000]:
            self.result.insert("", "end", values=(r.map_key, f"{r.planet_type} / {r.star_type} / 大小={r.planet_size} / 矿={r.mineral_density}"))

        self.status_var.set(f"当前结果数：{len(data)}（基于已展开节点）")

    def _export_preview(self) -> None:
        if self.current_planet is None:
            messagebox.showwarning("提示", "请先在左侧树中选中一个星球")
            return

        scale = int(self.preview_scale_var.get())
        default_name = f"planet_{self.current_planet.galaxy_pos[0]}_{self.current_planet.galaxy_pos[1]}__{self.current_planet.star_system_pos[0]}_{self.current_planet.star_system_pos[1]}__{self.current_planet.planet_pos[0]}_{self.current_planet.planet_pos[1]}.png"
        out = filedialog.asksaveasfilename(
            title="导出星球预览",
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg;*.jpeg")],
        )
        if not out:
            return
        try:
            path = export_planet_preview(self.current_planet, Path(out), tile_px=scale)
            self.status_var.set(f"已导出：{path}")
            messagebox.showinfo("完成", f"已导出高清预览\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))


def _verify_samples() -> None:
    samples = {
        "Weathering.MapOfPlanet#=1,4=14,93=24,31": (160, 60, 5, 12, 142, 5, "类地行星", "橙色恒星"),
        "Weathering.MapOfPlanet#=1,4=14,93=24,1": (80, 24, 2, 12, 71, 3, "冰冻星球", "橙色恒星"),
        "Weathering.MapOfPlanet#=97,11=18,1=20,6": (80, 60, 5, 12, 120, 7, "荒芜行星", "黄色恒星"),
    }
    for k, expected in samples.items():
        r = compute_planet_record(k)
        got = (
            r.seconds_for_a_day,
            r.days_for_a_year,
            r.days_for_a_month,
            r.month_for_a_year,
            r.planet_size,
            r.mineral_density,
            r.planet_type,
            r.star_type,
        )
        if got != expected:
            raise AssertionError(f"样例不匹配: {k}\n got={got}\n exp={expected}")


if __name__ == "__main__":
    _verify_samples()
    if os.environ.get("DISPLAY"):
        app = UniverseBrowser()
        app.mainloop()
    else:
        print("验证通过（无图形界面环境，跳过UI启动）")
