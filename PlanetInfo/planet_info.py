from __future__ import annotations

import json
import os
import inspect
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qs, unquote
from urllib.request import urlopen

MASK32 = 0xFFFFFFFF
UNIVERSE_SIZE = 100
GALAXY_SIZE = 100
STAR_SYSTEM_SIZE = 32
MONTH_FOR_A_YEAR = 12

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


@dataclass(frozen=True)
class PlanetRecord:
    map_key: str
    galaxy_x: int
    galaxy_y: int
    star_system_x: int
    star_system_y: int
    planet_x: int
    planet_y: int
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
    out: List[Tuple[int, int]] = []
    for item in coords:
        x, y = item.split(",")
        out.append((int(x), int(y)))
    if len(out) != 3:
        raise ValueError(map_key)
    return out[0], out[1], out[2]


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


def compute_planet_record(planet_map_key: str) -> PlanetRecord:
    g_pos, s_pos, p_pos = parse_map_key(planet_map_key)
    ss_map_key = build_map_key("MapOfStarSystem", [g_pos, s_pos])
    ss_hash = HashUtility.hash_string(ss_map_key)
    tile_hash = HashUtility.hash_tile(p_pos[0], p_pos[1], STAR_SYSTEM_SIZE, STAR_SYSTEM_SIZE, csharp_int32(ss_hash))

    main_star, second_star = _star_positions(ss_map_key)
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
        galaxy_x=g_pos[0],
        galaxy_y=g_pos[1],
        star_system_x=s_pos[0],
        star_system_y=s_pos[1],
        planet_x=p_pos[0],
        planet_y=p_pos[1],
        star_type=calculate_star_type(ss_map_key),
        planet_type=PLANET_TYPES[celestial],
        seconds_for_a_day=(60 * 8) // (1 + slowed),
        days_for_a_month=days_per_month,
        days_for_a_year=MONTH_FOR_A_YEAR * days_per_month,
        month_for_a_year=MONTH_FOR_A_YEAR,
        planet_size=50 + (self_hash % 100),
        mineral_density=3 + (HashUtility.add_salt(self_hash, 2641779086) % 27),
    )


def compute_planet_record_fast(
    gx: int,
    gy: int,
    sx: int,
    sy: int,
    px: int,
    py: int,
    star_type: str,
    tile_hash: int,
) -> PlanetRecord:
    """基于已知坐标与 tile_hash 快速构建 PlanetRecord，避免重复解析 map_key。"""
    map_key = build_map_key("MapOfPlanet", [(gx, gy), (sx, sy), (px, py)])
    hashcode = HashUtility.hash_uint(tile_hash)

    hashcode, v = HashUtility.hashed_ref(hashcode)
    if v % 50 != 0:
        raise ValueError("not playable terrestrial planet")
    hashcode, v = HashUtility.hashed_ref(hashcode)
    if v % 2 != 0:
        raise ValueError("not playable terrestrial planet")
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
    planet_hash = HashUtility.hash_string(map_key)
    self_hash = HashUtility.hash_string(slice_self_map_key_index(map_key))
    days_per_month = 2 + (planet_hash % 15)

    return PlanetRecord(
        map_key=map_key,
        galaxy_x=gx,
        galaxy_y=gy,
        star_system_x=sx,
        star_system_y=sy,
        planet_x=px,
        planet_y=py,
        star_type=star_type,
        planet_type=PLANET_TYPES[celestial],
        seconds_for_a_day=(60 * 8) // (1 + slowed),
        days_for_a_month=days_per_month,
        days_for_a_year=MONTH_FOR_A_YEAR * days_per_month,
        month_for_a_year=MONTH_FOR_A_YEAR,
        planet_size=50 + (self_hash % 100),
        mineral_density=3 + (HashUtility.add_salt(self_hash, 2641779086) % 27),
    )


def verify_samples() -> None:
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


class UniverseService:
    def __init__(self) -> None:
        self.preloaded = False
        self.preloading = False
        self.preload_seconds = 0.0
        self.planets_by_key: Dict[str, PlanetRecord] = {}
        self.galaxies: Dict[Tuple[int, int], Dict[str, object]] = {}
        self.systems: Dict[Tuple[int, int, int, int], Dict[str, object]] = {}
        self._preload_lock = threading.Lock()
        self._preload_thread: Optional[threading.Thread] = None
        self._preload_rows_done = 0
        self._preload_rows_total = UNIVERSE_SIZE

    def ensure_preload_started(self) -> None:
        with self._preload_lock:
            if self.preloaded or self.preloading:
                return
            self.preloading = True
            self._preload_thread = threading.Thread(target=self.preload_all, daemon=True)
            self._preload_thread.start()

    def preload_status(self) -> Dict[str, object]:
        progress = min(100, int((self._preload_rows_done / max(1, self._preload_rows_total)) * 100))
        if self.preloaded:
            progress = 100
        return {
            "ready": self.preloaded,
            "preloading": self.preloading,
            "progress_percent": progress,
            "rows_done": self._preload_rows_done,
            "rows_total": self._preload_rows_total,
            "galaxy_count": len(self.galaxies),
            "system_count": len(self.systems),
            "planet_count": len(self.planets_by_key),
            "preload_seconds": round(self.preload_seconds, 2),
        }

    @staticmethod
    def _scan_galaxy_rows(
        gy_start: int, gy_end: int
    ) -> Tuple[int, Dict[Tuple[int, int], Dict[str, object]], Dict[Tuple[int, int, int, int], Dict[str, object]], Dict[str, PlanetRecord]]:
        chunk_galaxies: Dict[Tuple[int, int], Dict[str, object]] = {}
        chunk_systems: Dict[Tuple[int, int, int, int], Dict[str, object]] = {}
        chunk_planets: Dict[str, PlanetRecord] = {}

        for gy in range(gy_start, gy_end):
            for gx in range(UNIVERSE_SIZE):
                if not is_galaxy((gx, gy)):
                    continue
                gkey = (gx, gy)
                chunk_galaxies[gkey] = {
                    "x": gx,
                    "y": gy,
                    "system_keys": [],
                    "planet_count": 0,
                    "star_type_counter": Counter(),
                }

                for sy in range(GALAXY_SIZE):
                    for sx in range(GALAXY_SIZE):
                        if not is_star_system((gx, gy), (sx, sy)):
                            continue
                        ss_map_key = build_map_key("MapOfStarSystem", [(gx, gy), (sx, sy)])
                        star_type = calculate_star_type(ss_map_key)

                        skey = (gx, gy, sx, sy)
                        chunk_galaxies[gkey]["system_keys"].append(skey)
                        chunk_galaxies[gkey]["star_type_counter"][star_type] += 1

                        chunk_systems[skey] = {
                            "gx": gx,
                            "gy": gy,
                            "sx": sx,
                            "sy": sy,
                            "star_type": star_type,
                            "planet_keys": [],
                            "planet_count": 0,
                            "planet_type_counter": Counter(),
                        }

                        ss_hash_i = csharp_int32(HashUtility.hash_string(ss_map_key))
                        main_star, second_star = _star_positions(ss_map_key)

                        for py in range(STAR_SYSTEM_SIZE):
                            for px in range(STAR_SYSTEM_SIZE):
                                is_star_tile = (px, py) == main_star or (second_star is not None and (px, py) == second_star)
                                tile_hash = HashUtility.hash_tile(px, py, STAR_SYSTEM_SIZE, STAR_SYSTEM_SIZE, ss_hash_i)
                                h = HashUtility.hash_uint(tile_hash)

                                if is_star_tile:
                                    continue
                                h = HashUtility.hash_uint(h)
                                if h % 50 != 0:
                                    continue
                                h = HashUtility.hash_uint(h)
                                if h % 2 != 0:
                                    continue

                                try:
                                    p = compute_planet_record_fast(gx, gy, sx, sy, px, py, star_type, tile_hash)
                                except ValueError:
                                    continue
                                chunk_planets[p.map_key] = p
                                chunk_systems[skey]["planet_keys"].append(p.map_key)
                                chunk_systems[skey]["planet_count"] += 1
                                chunk_systems[skey]["planet_type_counter"][p.planet_type] += 1
                                chunk_galaxies[gkey]["planet_count"] += 1

        return gy_end - gy_start, chunk_galaxies, chunk_systems, chunk_planets

    def preload_all(self) -> None:
        wait_thread: Optional[threading.Thread] = None
        with self._preload_lock:
            if self.preloaded:
                return
            if self.preloading and self._preload_thread is not None and self._preload_thread is not threading.current_thread():
                wait_thread = self._preload_thread
            else:
                self.preloading = True
                self._preload_thread = threading.current_thread()

        if wait_thread is not None:
            wait_thread.join()
            return

        start = time.time()
        self._preload_rows_done = 0
        print("[PlanetInfo] 开始预加载宇宙数据...")

        cpu = os.cpu_count() or 4
        workers = max(2, min(8, cpu))
        chunk_size = 2
        row_ranges = [(gy, min(UNIVERSE_SIZE, gy + chunk_size)) for gy in range(0, UNIVERSE_SIZE, chunk_size)]

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_map = {executor.submit(self._scan_galaxy_rows, gy0, gy1): (gy0, gy1) for gy0, gy1 in row_ranges}
            for future in as_completed(future_map):
                rows_done, row_galaxies, row_systems, row_planets = future.result()
                self.galaxies.update(row_galaxies)
                self.systems.update(row_systems)
                self.planets_by_key.update(row_planets)
                self._preload_rows_done += rows_done

                if self._preload_rows_done % 10 == 0 or self._preload_rows_done >= UNIVERSE_SIZE:
                    pct = int(self._preload_rows_done * 100 / UNIVERSE_SIZE)
                    print(
                        f"[PlanetInfo] 预加载进度: {self._preload_rows_done}/{UNIVERSE_SIZE} ({pct}%), "
                        f"星系={len(self.galaxies)}, 恒星系={len(self.systems)}, 行星={len(self.planets_by_key)}"
                    )

        self.preloaded = True
        self.preloading = False
        self._preload_thread = None
        self.preload_seconds = time.time() - start
        print(
            f"[PlanetInfo] 预加载完成: 星系={len(self.galaxies)}, 恒星系={len(self.systems)}, "
            f"行星={len(self.planets_by_key)}, 耗时={self.preload_seconds:.2f}s"
        )

    @staticmethod
    def _sort_rows(rows: List[Dict[str, object]], key: str, desc: bool) -> List[Dict[str, object]]:
        if not rows:
            return rows
        if key not in rows[0]:
            key = "x"
        if key == "x" and "y" in rows[0]:
            return sorted(rows, key=lambda r: (r["x"], r["y"]), reverse=desc)
        if key == "y" and "x" in rows[0]:
            return sorted(rows, key=lambda r: (r["y"], r["x"]), reverse=desc)
        return sorted(rows, key=lambda r: (r[key], r.get("x", 0), r.get("y", 0)), reverse=desc)

    def list_galaxies(self, sort_key: str = "x", desc: bool = False, search: str = "") -> List[Dict[str, object]]:
        self.preload_all()
        rows = [{"x": g["x"], "y": g["y"], "planet_count": g["planet_count"]} for g in self.galaxies.values()]
        if search:
            try:
                sx, sy = [int(x.strip()) for x in search.split(",")]
                rows = [r for r in rows if r["x"] == sx and r["y"] == sy]
            except Exception:
                rows = []
        return self._sort_rows(rows, sort_key, desc)

    def galaxy_info(self, gx: int, gy: int) -> Dict[str, object]:
        self.preload_all()
        g = self.galaxies[(gx, gy)]
        return {
            "level": "galaxy",
            "x": gx,
            "y": gy,
            "planet_count": g["planet_count"],
            "star_type_stats": dict(g["star_type_counter"]),
            "star_system_count": len(g["system_keys"]),
        }

    def list_systems(self, gx: int, gy: int, sort_key: str = "x", desc: bool = False, search: str = "") -> List[Dict[str, object]]:
        self.preload_all()
        g = self.galaxies[(gx, gy)]
        rows = []
        for skey in g["system_keys"]:
            s = self.systems[skey]
            rows.append({
                "x": s["sx"],
                "y": s["sy"],
                "star_type": s["star_type"],
                "planet_count": s["planet_count"],
            })
        if search:
            try:
                sx, sy = [int(x.strip()) for x in search.split(",")]
                rows = [r for r in rows if r["x"] == sx and r["y"] == sy]
            except Exception:
                rows = []
        return self._sort_rows(rows, sort_key, desc)

    def system_info(self, gx: int, gy: int, sx: int, sy: int) -> Dict[str, object]:
        self.preload_all()
        s = self.systems[(gx, gy, sx, sy)]
        return {
            "level": "system",
            "gx": gx,
            "gy": gy,
            "x": sx,
            "y": sy,
            "star_type": s["star_type"],
            "planet_count": s["planet_count"],
            "planet_type_stats": dict(s["planet_type_counter"]),
        }

    def list_planets(self, gx: int, gy: int, sx: int, sy: int, sort_key: str = "planet_x", desc: bool = False) -> List[Dict[str, object]]:
        self.preload_all()
        s = self.systems[(gx, gy, sx, sy)]
        rows = [asdict(self.planets_by_key[k]) for k in s["planet_keys"]]
        if rows and sort_key not in rows[0]:
            sort_key = "planet_x"
        rows = sorted(rows, key=lambda x: x[sort_key], reverse=desc)
        return rows

    def planet_info(self, map_key: str) -> Dict[str, object]:
        self.preload_all()
        return asdict(self.planets_by_key[map_key])

    def app_info(self) -> Dict[str, object]:
        self.preload_all()
        return {
            "galaxy_count": len(self.galaxies),
            "system_count": len(self.systems),
            "planet_count": len(self.planets_by_key),
            "preload_seconds": round(self.preload_seconds, 2),
        }

    def list_system_rankings(
        self,
        sort_key: str = "overall_area",
        desc: Optional[bool] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> Dict[str, object]:
        self.preload_all()
        rows: List[Dict[str, object]] = []
        threshold_t = 50

        for s in self.systems.values():
            planets = [self.planets_by_key[k] for k in s["planet_keys"]]
            if not planets:
                continue

            overall_area = sum(p.planet_size**2 for p in planets)
            avg_mineral_density = sum(p.mineral_density for p in planets) / len(planets)
            planet_count = len(planets)
            avg_area = overall_area / planet_count
            base_value = sum((p.planet_size**2) ** 0.5 / p.mineral_density for p in planets)
            creep_penalty = planet_count / math.log2((avg_area / threshold_t) + 2)
            score_v = base_value * creep_penalty
            rows.append(
                {
                    "gx": s["gx"],
                    "gy": s["gy"],
                    "sx": s["sx"],
                    "sy": s["sy"],
                    "star_type": s["star_type"],
                    "planet_count": s["planet_count"],
                    "overall_area": overall_area,
                    "avg_area": round(avg_area, 2),
                    "avg_mineral_density": round(avg_mineral_density, 2),
                    "base_value": round(base_value, 4),
                    "cost_penalty": round(creep_penalty, 4),
                    "score_v": round(score_v, 4),
                    "planet_type_stats": dict(s["planet_type_counter"]),
                }
            )

        valid_keys = {"overall_area", "avg_mineral_density", "score_v", "planet_count", "gx", "gy", "sx", "sy"}
        if sort_key not in valid_keys:
            sort_key = "overall_area"

        if desc is None:
            desc = sort_key != "avg_mineral_density"

        rows = sorted(
            rows,
            key=lambda r: (r[sort_key], r["gx"], r["gy"], r["sx"], r["sy"]),
            reverse=desc,
        )

        page = max(1, page)
        page_size = max(1, min(100, page_size))
        total = len(rows)
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages)
        begin = (page - 1) * page_size
        end = begin + page_size
        return {
            "rows": rows[begin:end],
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "sort_key": sort_key,
            "desc": desc,
        }


HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Weathering Universe Explorer</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
  <script type="module" src="https://unpkg.com/@fluentui/web-components@2.6.1/dist/web-components.min.js"></script>
  <style>
    :root { --bg:#071025; --panel:#0f1a30; --line:#24385a; --txt:#e8f0ff; --sub:#8dc6ff; }
    * { box-sizing:border-box; }
    body { margin:0; background:radial-gradient(circle at 10% 10%, #15284c 0%, var(--bg) 45%); color:var(--txt); font-family:Segoe UI,system-ui,sans-serif; overflow:hidden; }
    .app { display:flex; flex-direction:column; height:100vh; padding:12px; gap:12px; }
    .app.hidden { display:none; }
    .topbar { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:10px 14px; border:1px solid var(--line); border-radius:12px; background:rgba(15,26,48,.95); }
    .brand { font-size:14px; color:var(--sub); letter-spacing:.04em; font-weight:700; }
    .tabs { display:flex; gap:8px; }
    .tab-btn { border:1px solid #2f4e7b; border-radius:10px; background:#122240; color:#cde3ff; padding:8px 12px; cursor:pointer; }
    .tab-btn.active { border-color:#4f80cb; background:#1a315a; color:#fff; }
    .view { display:none; min-height:0; flex:1; }
    .view.active { display:grid; }
    .view.nav-view { --nav-width:340px; grid-template-columns:minmax(300px, var(--nav-width)) 10px minmax(0,1fr); gap:0; align-items:stretch; }
    .view.rank-view { grid-template-columns:1fr; gap:12px; }
    .panel { overflow:auto; padding:14px; background:rgba(15,26,48,.9); border:1px solid var(--line); border-radius:14px; }
    .nav-pane { min-width:0; }
    .nav-side { border-top-right-radius:0; border-bottom-right-radius:0; border-right-width:0; }
    .nav-main { border-top-left-radius:0; border-bottom-left-radius:0; border-left-width:0; }
    .nav-divider {
      cursor:col-resize;
      user-select:none;
      position:relative;
      background:linear-gradient(180deg, rgba(36,56,90,.9), rgba(18,34,64,.95));
      border-left:1px solid #355281;
      border-right:1px solid #1f3558;
    }
    .nav-divider::after {
      content:'';
      position:absolute;
      left:50%; top:50%; transform:translate(-50%,-50%);
      width:3px; height:36px; border-radius:999px;
      background:#79a8ea;
      box-shadow:0 0 0 1px rgba(20,43,82,.5);
    }
    .nav-divider.dragging::after { background:#a7ccff; }
    .title { color:var(--sub); margin:0 0 12px; font-size:16px; font-weight:700; letter-spacing:.04em; }
    .row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:10px; }
    .toolbar { display:flex; align-items:center; gap:8px; margin-bottom:10px; flex-wrap:wrap; }
    .toolbar .hint { white-space:nowrap; }
    .toolbar-select { flex:1 1 120px; min-width:118px; }
    .toolbar-search { flex:1 1 88px; min-width:88px; }
    .node { padding:11px 12px; border-radius:10px; border:1px solid #2a4068; margin-bottom:8px; cursor:pointer; background:#0e1930; transition:.18s ease; }
    .node:hover { background:#142548; border-color:#3f6bad; transform:translateY(-1px); }
    .rank-node { position:relative; padding-right:20px; }
    .rank-meta { color:#9bb6dd; font-size:12px; margin-top:4px; }
    .rank-hover-panel { position:fixed; left:0; top:0; width:290px; background:#0a162f; border:1px solid #466da6; border-radius:10px; padding:8px; display:none; z-index:9999; box-shadow:0 8px 24px rgba(0,0,0,.45); pointer-events:none; }
    .pager { display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:10px; }
    .hint { color:#9bb6dd; font-size:12px; }
    .kv { margin:9px 0; line-height:1.5; }
    .pill { display:inline-block; margin:4px 6px 4px 0; padding:5px 9px; border:1px solid var(--line); border-radius:999px; background:#132748; }
    .btn-icon { border:1px solid var(--line); border-radius:8px; background:#132746; color:var(--txt); padding:7px 10px; cursor:pointer; }
    .btn-icon:hover { background:#1b3763; }
    .loading-overlay { position:fixed; inset:0; display:flex; align-items:center; justify-content:center; background:linear-gradient(180deg,#020617,#071025); z-index:99; }
    .loading-card { width:min(560px,88vw); background:rgba(15,26,48,.92); border:1px solid var(--line); border-radius:14px; padding:22px; }
    .loading-title { margin:0 0 8px; color:var(--sub); font-size:20px; }
    .progress { height:12px; border-radius:999px; border:1px solid var(--line); overflow:hidden; background:#0b1326; }
    .bar { height:100%; width:4%; background:linear-gradient(90deg,#3b82f6,#93c5fd); }
  </style>
</head>
<body>
<div id="loadingOverlay" class="loading-overlay">
  <div class="loading-card">
    <h2 class="loading-title">加载中</h2>
    <div id="loadingStats" class="hint" style="margin-bottom:8px">正在构建宇宙索引...</div>
    <div class="progress"><div id="loadingBar" class="bar"></div></div>
  </div>
</div>

<div id="app" class="app hidden">
  <header class="topbar">
    <div class="brand">Weathering Universe Explorer</div>
    <div class="tabs">
      <button id="tabNav" class="tab-btn active">导航检索</button>
      <button id="tabRank" class="tab-btn">恒星系排行</button>
    </div>
  </header>

  <section id="navView" class="view nav-view active">
    <aside class="panel nav-pane nav-side">
      <h3 class="title">导航</h3>
      <div class="row">
        <button id="backBtn" class="btn-icon"><i class="bi bi-arrow-left-circle"></i> 返回</button>
        <span id="breadcrumb" class="hint">宇宙 / 星系列表</span>
      </div>

      <div id="searchBlock" class="toolbar">
        <fluent-text-field id="coordSearch" class="toolbar-search" placeholder="x,y"></fluent-text-field>
        <button id="searchBtn" class="btn-icon"><i class="bi bi-search"></i></button>
        <fluent-select id="sortKey" class="toolbar-select"></fluent-select>
        <button id="sortDirBtn" class="btn-icon" title="切换升降序"><i id="sortDirIcon" class="bi bi-sort-down-alt"></i></button>
        <span id="sortLabel" class="hint">升序</span>
      </div>

      <div id="list"></div>
    </aside>

    <div id="navDivider" class="nav-divider" title="拖拽调整左右面板宽度"></div>

    <main class="panel nav-pane nav-main">
      <h3 class="title">具体信息</h3>
      <div id="info" class="hint">启动中：正在加载全部星球数据...</div>
    </main>
  </section>

  <section id="rankView" class="view rank-view">
    <main class="panel">
      <h3 class="title">恒星系综合排行（全宇宙）</h3>
      <div class="toolbar" style="grid-template-columns:auto auto auto auto 1fr;">
        <span class="hint">排序：</span>
        <fluent-select id="rankSortKey" style="width:220px"></fluent-select>
        <button id="rankSortDirBtn" class="btn-icon" title="切换升降序"><i id="rankSortDirIcon" class="bi bi-sort-up-alt"></i></button>
        <button id="rankRefreshBtn" class="btn-icon">刷新</button>
        <span id="rankSortDesc" class="hint"></span>
      </div>
      <div class="pager">
        <div class="row" style="margin:0">
          <button id="rankPrev" class="btn-icon">上一页</button>
          <button id="rankNext" class="btn-icon">下一页</button>
        </div>
        <span id="rankPageInfo" class="hint"></span>
      </div>
      <div id="rankList"></div>
      <div id="rankHoverPanel" class="rank-hover-panel"></div>
    </main>
  </section>
</div>

<script>
const API = '/api';
const appRoot = document.getElementById('app');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingStats = document.getElementById('loadingStats');
const loadingBar = document.getElementById('loadingBar');
const info = document.getElementById('info');
const list = document.getElementById('list');
const breadcrumb = document.getElementById('breadcrumb');
const sortKey = document.getElementById('sortKey');
const sortDirIcon = document.getElementById('sortDirIcon');
const sortLabel = document.getElementById('sortLabel');
const tabNav = document.getElementById('tabNav');
const tabRank = document.getElementById('tabRank');
const navView = document.getElementById('navView');
const rankView = document.getElementById('rankView');
const rankList = document.getElementById('rankList');
const rankSortKey = document.getElementById('rankSortKey');
const rankSortDirIcon = document.getElementById('rankSortDirIcon');
const rankSortDesc = document.getElementById('rankSortDesc');
const rankPageInfo = document.getElementById('rankPageInfo');
const rankHoverPanel = document.getElementById('rankHoverPanel');
const navDivider = document.getElementById('navDivider');
const searchBlock = document.getElementById('searchBlock');
const forceReady = new URLSearchParams(window.location.search).get('ready') === '1';

let state = {
  tab: 'nav',
  level: 'galaxy',
  gx: null, gy: null,
  sx: null, sy: null,
  sort_key: 'x',
  desc: false,
  rank: {
    page: 1,
    page_size: 25,
    sort_key: 'overall_area',
    desc: true,
    total_pages: 1,
  },
};

function defaultRankDesc(sortKey){
  return sortKey !== 'avg_mineral_density';
}

function setSortIndicator(){
  sortDirIcon.className = state.desc ? 'bi bi-sort-up-alt' : 'bi bi-sort-down-alt';
  sortLabel.textContent = state.desc ? '降序' : '升序';
}

function setRankSortIndicator(){
  rankSortDirIcon.className = state.rank.desc ? 'bi bi-sort-up-alt' : 'bi bi-sort-down-alt';
  rankSortDesc.textContent = state.rank.sort_key === 'avg_mineral_density'
    ? `当前${state.rank.desc ? '降序（高密度优先）' : '升序（低密度优先）'}`
    : `当前${state.rank.desc ? '降序' : '升序'}`;
}

function switchTab(tab){
  state.tab = tab;
  const navActive = tab === 'nav';
  tabNav.classList.toggle('active', navActive);
  tabRank.classList.toggle('active', !navActive);
  navView.classList.toggle('active', navActive);
  rankView.classList.toggle('active', !navActive);
}

function setSortOptions(level){
  sortKey.innerHTML = '';
  const keys = level === 'galaxy'
    ? ['x','y','planet_count']
    : level === 'system'
    ? ['x','y','planet_count']
    : ['planet_x','planet_y','planet_size','mineral_density','seconds_for_a_day'];
  for (const k of keys){
    const o = document.createElement('fluent-option');
    o.value = k;
    o.textContent = k;
    sortKey.appendChild(o);
  }
  if (!keys.includes(state.sort_key)) state.sort_key = keys[0];
  sortKey.value = state.sort_key;
}

function parseCoordInput(raw){
  const parts = raw.split(',').map(v => v.trim());
  if (parts.length !== 2) return null;
  const x = Number(parts[0]);
  const y = Number(parts[1]);
  if (!Number.isInteger(x) || !Number.isInteger(y)) return null;
  return {x, y};
}

function renderInfo(data){
  if (data.level === 'galaxy') {
    const starStats = Object.entries(data.star_type_stats).map(([k,v])=>`<span class='pill'>${k}: ${v}</span>`).join('');
    info.innerHTML = `
      <div class='kv'><b>当前层级:</b> 星系</div>
      <div class='kv'><b>坐标:</b> (${data.x}, ${data.y})</div>
      <div class='kv'><b>恒星系数量:</b> ${data.star_system_count}</div>
      <div class='kv'><b>星球数量:</b> ${data.planet_count}</div>
      <div class='kv'><b>恒星类型统计:</b><br>${starStats || '无'}</div>
    `;
  } else if (data.level === 'system') {
    const pStats = Object.entries(data.planet_type_stats).map(([k,v])=>`<span class='pill'>${k}: ${v}</span>`).join('');
    info.innerHTML = `
      <div class='kv'><b>当前层级:</b> 恒星系</div>
      <div class='kv'><b>坐标:</b> 星系(${data.gx}, ${data.gy}) / 恒星系(${data.x}, ${data.y})</div>
      <div class='kv'><b>恒星类型:</b> ${data.star_type}</div>
      <div class='kv'><b>星球数量:</b> ${data.planet_count}</div>
      <div class='kv'><b>行星类型统计:</b><br>${pStats || '无'}</div>
    `;
  } else {
    info.innerHTML = `
      <div class='kv'><b>当前层级:</b> 行星</div>
      <div class='kv'><b>MapKey:</b> ${data.map_key}</div>
      <div class='kv'><b>坐标:</b> 星系(${data.galaxy_x},${data.galaxy_y}) / 恒星系(${data.star_system_x},${data.star_system_y}) / 行星(${data.planet_x},${data.planet_y})</div>
      <div class='kv'><b>恒星类型:</b> ${data.star_type}</div>
      <div class='kv'><b>行星类型:</b> ${data.planet_type}</div>
      <div class='kv'><b>昼夜周期(秒):</b> ${data.seconds_for_a_day}</div>
      <div class='kv'><b>月份天数:</b> ${data.days_for_a_month}</div>
      <div class='kv'><b>年份天数:</b> ${data.days_for_a_year}</div>
      <div class='kv'><b>星球大小:</b> ${data.planet_size}</div>
      <div class='kv'><b>矿物稀疏度:</b> ${data.mineral_density}</div>
    `;
  }
}

async function getJson(url){
  const r = await fetch(url);
  if (!r.ok) throw new Error(await r.text());
  return await r.json();
}

async function loadList(search=''){
  list.innerHTML = '<div class="hint">加载中...</div>';

  if (state.level === 'galaxy') {
    breadcrumb.textContent = '宇宙 / 星系列表';
    const rows = await getJson(`${API}/galaxies?sort_key=${state.sort_key}&desc=${state.desc?1:0}&search=${encodeURIComponent(search)}`);
    list.innerHTML = '';
    for (const r of rows){
      const div = document.createElement('div');
      div.className = 'node';
      div.textContent = `星系 ${r.x},${r.y} · 星球 ${r.planet_count}`;
      div.onclick = async ()=>{
        state.level = 'system';
        state.gx = r.x; state.gy = r.y;
        state.sort_key = 'x';
        setSortOptions('system');
        renderInfo(await getJson(`${API}/galaxy_info?gx=${r.x}&gy=${r.y}`));
        await loadList('');
      };
      list.appendChild(div);
    }
    return;
  }

  if (state.level === 'system') {
    breadcrumb.textContent = `宇宙 / 星系(${state.gx},${state.gy}) / 恒星系列表`;
    const rows = await getJson(`${API}/systems?gx=${state.gx}&gy=${state.gy}&sort_key=${state.sort_key}&desc=${state.desc?1:0}&search=${encodeURIComponent(search)}`);
    list.innerHTML = '';
    for (const r of rows){
      const div = document.createElement('div');
      div.className = 'node';
      div.textContent = `恒星系 ${r.x},${r.y} · ${r.star_type} · 星球 ${r.planet_count}`;
      div.onclick = async ()=>{
        state.level = 'planet';
        state.sx = r.x; state.sy = r.y;
        state.sort_key = 'planet_x';
        setSortOptions('planet');
        renderInfo(await getJson(`${API}/system_info?gx=${state.gx}&gy=${state.gy}&sx=${r.x}&sy=${r.y}`));
        await loadList('');
      };
      list.appendChild(div);
    }
    return;
  }

  breadcrumb.textContent = `宇宙 / 星系(${state.gx},${state.gy}) / 恒星系(${state.sx},${state.sy}) / 行星列表`;
  const rows = await getJson(`${API}/planets?gx=${state.gx}&gy=${state.gy}&sx=${state.sx}&sy=${state.sy}&sort_key=${state.sort_key}&desc=${state.desc?1:0}`);
  list.innerHTML = '';
  for (const p of rows){
    const div = document.createElement('div');
    div.className = 'node';
    div.textContent = `行星 ${p.planet_x},${p.planet_y} · ${p.planet_type} · 大小 ${p.planet_size}`;
    div.onclick = ()=> renderInfo(p);
    list.appendChild(div);
  }
}

function formatStats(stats){
  const parts = Object.entries(stats || {}).sort((a,b)=>b[1]-a[1]).slice(0,4).map(([k,v])=>`${k}:${v}`);
  return parts.join(' · ') || '无';
}

function updateRankHoverPanelPosition(event){
  const offset = 14;
  const panelWidth = 290;
  const panelHeight = 170;
  let left = event.clientX + offset;
  let top = event.clientY + offset;
  if (left + panelWidth > window.innerWidth - 8) left = event.clientX - panelWidth - offset;
  if (top + panelHeight > window.innerHeight - 8) top = event.clientY - panelHeight - offset;
  rankHoverPanel.style.left = `${Math.max(8, left)}px`;
  rankHoverPanel.style.top = `${Math.max(8, top)}px`;
}

function showRankHoverPanel(r, event){
  rankHoverPanel.innerHTML = `
    <div><b>位置</b>：星系(${r.gx},${r.gy}) / 恒星系(${r.sx},${r.sy})</div>
    <div><b>恒星</b>：${r.star_type}</div>
    <div><b>组成</b>：${formatStats(r.planet_type_stats)}</div>
    <div><b>S总面积</b>：${r.overall_area}（均值 ${r.avg_area}）</div>
    <div><b>A平均矿物丰度</b>：${r.avg_mineral_density}</div>
    <div><b>Σ(√Si/Ai)</b>：${r.base_value}</div>
    <div><b>惩罚项</b>：N/log2(S̄/T+2) = ${r.cost_penalty}（T=50）</div>
    <div><b>Vsys</b>：${r.score_v}</div>
  `;
  rankHoverPanel.style.display = 'block';
  updateRankHoverPanelPosition(event);
}

function hideRankHoverPanel(){
  rankHoverPanel.style.display = 'none';
}

function getMinNavWidth(){
  return Math.max(300, Math.ceil(searchBlock.scrollWidth + 24));
}

function setNavWidth(px){
  const rect = navView.getBoundingClientRect();
  const minWidth = getMinNavWidth();
  const maxWidth = Math.max(minWidth + 40, Math.floor(rect.width * 0.7));
  const next = Math.max(minWidth, Math.min(maxWidth, Math.floor(px)));
  navView.style.setProperty('--nav-width', `${next}px`);
}

function autoFitNavWidth(){
  const minWidth = getMinNavWidth();
  setNavWidth(minWidth);
}

function bindNavDividerDrag(){
  let dragging = false;
  navDivider.addEventListener('mousedown', (event)=>{
    event.preventDefault();
    dragging = true;
    navDivider.classList.add('dragging');
  });
  window.addEventListener('mousemove', (event)=>{
    if (!dragging) return;
    const rect = navView.getBoundingClientRect();
    setNavWidth(event.clientX - rect.left);
  });
  window.addEventListener('mouseup', ()=>{
    if (!dragging) return;
    dragging = false;
    navDivider.classList.remove('dragging');
  });
  navDivider.addEventListener('dblclick', autoFitNavWidth);
  window.addEventListener('resize', ()=> setNavWidth(parseFloat(getComputedStyle(navView).getPropertyValue('--nav-width')) || 340));
}

async function loadRankings(){
  hideRankHoverPanel();
  rankList.innerHTML = '<div class="hint">加载排行中...</div>';
  const data = await getJson(`${API}/system_rankings?sort_key=${state.rank.sort_key}&desc=${state.rank.desc?1:0}&page=${state.rank.page}&page_size=${state.rank.page_size}`);
  state.rank.page = data.page;
  state.rank.total_pages = data.total_pages;
  rankPageInfo.textContent = `第 ${data.page}/${data.total_pages} 页 · 共 ${data.total} 个恒星系`;
  setRankSortIndicator();

  rankList.innerHTML = '';
  data.rows.forEach((r, idx)=>{
    const rankNo = (data.page - 1) * data.page_size + idx + 1;
    const div = document.createElement('div');
    div.className = 'node rank-node';
    div.innerHTML = `
      <div><b>#${rankNo}</b> 星系(${r.gx},${r.gy}) / 恒星系(${r.sx},${r.sy}) · ${r.star_type}</div>
      <div class='rank-meta'>S=${r.overall_area} · A=${r.avg_mineral_density} · Vsys=${r.score_v} · 行星数=${r.planet_count}</div>
    `;
    div.addEventListener('mouseenter', (event)=> showRankHoverPanel(r, event));
    div.addEventListener('mousemove', (event)=> updateRankHoverPanelPosition(event));
    div.addEventListener('mouseleave', hideRankHoverPanel);
    rankList.appendChild(div);
  });
}

async function jumpBySearch(){
  const search = document.getElementById('coordSearch').value.trim();
  if (!search) {
    await loadList('');
    return;
  }
  const c = parseCoordInput(search);
  if (!c) {
    list.innerHTML = '<div class="hint">请输入合法坐标，例如 12,34</div>';
    return;
  }

  if (state.level === 'galaxy') {
    const r = await getJson(`${API}/galaxies?search=${encodeURIComponent(search)}`);
    if (!r.length) {
      list.innerHTML = '<div class="hint">未找到该星系</div>';
      return;
    }
    state.level = 'system';
    state.gx = c.x; state.gy = c.y;
    state.sort_key = 'x';
    state.desc = false;
    setSortIndicator();
    setSortOptions('system');
    renderInfo(await getJson(`${API}/galaxy_info?gx=${c.x}&gy=${c.y}`));
    await loadList('');
    return;
  }

  if (state.level === 'system') {
    const r = await getJson(`${API}/systems?gx=${state.gx}&gy=${state.gy}&search=${encodeURIComponent(search)}`);
    if (!r.length) {
      list.innerHTML = '<div class="hint">未找到该恒星系</div>';
      return;
    }
    state.level = 'planet';
    state.sx = c.x; state.sy = c.y;
    state.sort_key = 'planet_x';
    state.desc = false;
    setSortIndicator();
    setSortOptions('planet');
    renderInfo(await getJson(`${API}/system_info?gx=${state.gx}&gy=${state.gy}&sx=${c.x}&sy=${c.y}`));
    await loadList('');
    return;
  }

  await loadList('');
}

async function init() {
  bindNavDividerDrag();
  autoFitNavWidth();

  if (!forceReady) {
    const loadingStart = Date.now();
    const MIN_LOADING_MS = 1500;
    let sawPreloading = false;
    while (true) {
      const status = await getJson(`${API}/preload_status`);
      const pct = status.progress_percent || 0;
      if (status.preloading || !status.ready) sawPreloading = true;
      loadingStats.textContent = `进度 ${pct}% (${status.rows_done}/${status.rows_total}) · 星系: ${status.galaxy_count} · 恒星系: ${status.system_count} · 行星: ${status.planet_count}`;
      loadingBar.style.width = `${Math.max(4, pct)}%`;
      const elapsed = Date.now() - loadingStart;
      const canEnter = status.ready && elapsed >= MIN_LOADING_MS && (sawPreloading || pct >= 100);
      if (canEnter) {
        loadingOverlay.style.display = 'none';
        appRoot.classList.remove('hidden');
        info.innerHTML = `<b>已加载</b><br>星系: ${status.galaxy_count} · 恒星系: ${status.system_count} · 行星: ${status.planet_count}`;
        break;
      }
      await new Promise(r => setTimeout(r, 300));
    }
  } else {
    loadingOverlay.style.display = 'none';
    appRoot.classList.remove('hidden');
    const app = await getJson(`${API}/app_info`);
    info.innerHTML = `<b>全部数据已加载完成</b><br>星系: ${app.galaxy_count} · 恒星系: ${app.system_count} · 行星: ${app.planet_count}<br>加载耗时: ${app.preload_seconds}s`;
  }

  setSortOptions('galaxy');
  setSortIndicator();
  rankSortKey.innerHTML = `
    <fluent-option value="overall_area">overall_area (总面积S)</fluent-option>
    <fluent-option value="avg_mineral_density">avg_mineral_density (矿物稀疏度A)</fluent-option>
    <fluent-option value="score_v">Vsys = Σ(√Si/Ai) × N/log2(S̄/T+2)</fluent-option>
  `;
  rankSortKey.value = state.rank.sort_key;
  setRankSortIndicator();
  await loadList('');
}

document.getElementById('sortKey').onchange = async (e)=>{
  state.sort_key = e.target.value;
  await loadList(document.getElementById('coordSearch').value.trim());
};

document.getElementById('sortDirBtn').onclick = async ()=>{
  state.desc = !state.desc;
  setSortIndicator();
  await loadList(document.getElementById('coordSearch').value.trim());
};

document.getElementById('searchBtn').onclick = async ()=>{
  await jumpBySearch();
};

document.getElementById('coordSearch').addEventListener('keydown', async (event)=>{
  if (event.key === 'Enter') {
    await jumpBySearch();
  }
});

document.getElementById('backBtn').onclick = async ()=>{
  if (state.level === 'planet') {
    state.level = 'system';
    state.sort_key = 'x';
    setSortOptions('system');
    renderInfo(await getJson(`${API}/galaxy_info?gx=${state.gx}&gy=${state.gy}`));
  } else if (state.level === 'system') {
    state.level = 'galaxy';
    state.gx = null; state.gy = null;
    state.sort_key = 'x';
    setSortOptions('galaxy');
    const app = await getJson(`${API}/app_info`);
    info.innerHTML = `<b>全部数据已加载完成</b><br>星系: ${app.galaxy_count} · 恒星系: ${app.system_count} · 行星: ${app.planet_count}<br>加载耗时: ${app.preload_seconds}s`;
  }
  state.desc = false;
  setSortIndicator();
  await loadList('');
};

tabNav.onclick = ()=> switchTab('nav');
tabRank.onclick = async ()=>{
  switchTab('rank');
  await loadRankings();
};

rankSortKey.onchange = async (e)=>{
  state.rank.sort_key = e.target.value;
  state.rank.desc = defaultRankDesc(state.rank.sort_key);
  state.rank.page = 1;
  await loadRankings();
};

document.getElementById('rankSortDirBtn').onclick = async ()=>{
  state.rank.desc = !state.rank.desc;
  state.rank.page = 1;
  await loadRankings();
};

document.getElementById('rankRefreshBtn').onclick = async ()=>{
  await loadRankings();
};

document.getElementById('rankPrev').onclick = async ()=>{
  if (state.rank.page <= 1) return;
  state.rank.page -= 1;
  await loadRankings();
};

document.getElementById('rankNext').onclick = async ()=>{
  if (state.rank.page >= state.rank.total_pages) return;
  state.rank.page += 1;
  await loadRankings();
};

init();
</script>
</body>
</html>
"""


LOADING_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Weathering PlanetInfo Loading</title>
  <style>
    :root { --bg:#071025; --panel:#0f1a30; --line:#24385a; --txt:#e8f0ff; --sub:#8dc6ff; }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--bg); color:var(--txt); font-family:Segoe UI,system-ui,sans-serif; }
    .wrap { width:100vw; height:100vh; display:flex; align-items:center; justify-content:center; padding:10px; }
    .card { width:100%; max-width:460px; border:1px solid var(--line); border-radius:12px; background:rgba(15,26,48,.95); padding:16px; }
    .title { color:var(--sub); font-size:16px; margin:0 0 8px; }
    .hint { color:#9bb6dd; font-size:12px; margin-bottom:8px; }
    .progress { height:12px; border-radius:999px; border:1px solid var(--line); overflow:hidden; background:#0b1326; }
    .bar { height:100%; width:4%; background:linear-gradient(90deg,#3b82f6,#93c5fd); transition:width .2s ease; }
  </style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <h3 class="title">加载中</h3>
    <div id="loadingStats" class="hint">正在构建宇宙索引...</div>
    <div class="progress"><div id="loadingBar" class="bar"></div></div>
  </div>
</div>
<script>
const stats = document.getElementById('loadingStats');
const bar = document.getElementById('loadingBar');
async function poll(){
  try {
    const r = await fetch('/api/preload_status');
    if (!r.ok) throw new Error('status not ok');
    const d = await r.json();
    const pct = d.progress_percent || 0;
    bar.style.width = `${Math.max(4, pct)}%`;
    stats.textContent = `进度 ${pct}% (${d.rows_done}/${d.rows_total}) · 星系: ${d.galaxy_count} · 恒星系: ${d.system_count} · 行星: ${d.planet_count}`;
  } catch (e) {
    stats.textContent = '正在连接本地服务...';
  }
}
setInterval(poll, 250);
poll();
</script>
</body>
</html>
"""


class AppHTTP(BaseHTTPRequestHandler):
    service = UniverseService()

    def _json(self, data: object, status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _html(self, data: str, status: int = 200) -> None:
        raw = data.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        path, _, query = self.path.partition("?")
        params_raw = parse_qs(query, keep_blank_values=True)
        params = {k: unquote(v[0]) for k, v in params_raw.items() if v}

        try:
            if path == "/":
                self.service.ensure_preload_started()
                self._html(HTML)
                return
            if path == "/loading":
                self.service.ensure_preload_started()
                self._html(LOADING_HTML)
                return
            if path == "/api/preload_status":
                self.service.ensure_preload_started()
                self._json(self.service.preload_status())
                return
            if path == "/api/app_info":
                self._json(self.service.app_info())
                return
            if path == "/api/galaxies":
                self._json(
                    self.service.list_galaxies(
                        sort_key=params.get("sort_key", "x"),
                        desc=params.get("desc", "0") == "1",
                        search=params.get("search", ""),
                    )
                )
                return
            if path == "/api/galaxy_info":
                self._json(self.service.galaxy_info(int(params["gx"]), int(params["gy"])))
                return
            if path == "/api/systems":
                self._json(
                    self.service.list_systems(
                        int(params["gx"]),
                        int(params["gy"]),
                        sort_key=params.get("sort_key", "x"),
                        desc=params.get("desc", "0") == "1",
                        search=params.get("search", ""),
                    )
                )
                return
            if path == "/api/system_info":
                self._json(self.service.system_info(int(params["gx"]), int(params["gy"]), int(params["sx"]), int(params["sy"])))
                return
            if path == "/api/planets":
                self._json(
                    self.service.list_planets(
                        int(params["gx"]),
                        int(params["gy"]),
                        int(params["sx"]),
                        int(params["sy"]),
                        sort_key=params.get("sort_key", "planet_x"),
                        desc=params.get("desc", "0") == "1",
                    )
                )
                return
            if path == "/api/planet":
                self._json(self.service.planet_info(params["map_key"]))
                return
            if path == "/api/system_rankings":
                desc_value = params.get("desc")
                desc = None if desc_value is None else desc_value == "1"
                self._json(
                    self.service.list_system_rankings(
                        sort_key=params.get("sort_key", "overall_area"),
                        desc=desc,
                        page=int(params.get("page", "1")),
                        page_size=int(params.get("page_size", "25")),
                    )
                )
                return
            self._json({"error": "not found"}, status=404)
        except Exception as e:
            self._json({"error": str(e)}, status=400)


def run_server(port: int = 8765) -> ThreadingHTTPServer:
    verify_samples()
    server = ThreadingHTTPServer(("0.0.0.0", port), AppHTTP)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


def create_window_compat(webview_module, *args, **kwargs):
    """兼容不同 pywebview 版本的 create_window 参数。"""
    options = dict(kwargs)

    # 先基于函数签名过滤（如果当前 pywebview 暴露了可检查签名）
    try:
        signature = inspect.signature(webview_module.create_window)
        supported = set(signature.parameters.keys())
        for key in list(options.keys()):
            if key not in supported:
                print(f"[PlanetInfo] 当前 pywebview 签名不包含参数 '{key}'，已自动降级兼容")
                options.pop(key)
    except Exception:
        # 某些实现无法反射签名，继续走异常兜底重试逻辑
        pass

    while True:
        try:
            return webview_module.create_window(*args, **options)
        except TypeError as exc:
            msg = str(exc)
            token = "unexpected keyword argument "
            if token not in msg:
                raise
            bad_key = msg.split(token, 1)[1].strip().strip("'\"")
            if bad_key not in options:
                raise
            print(f"[PlanetInfo] 当前 pywebview 不支持参数 '{bad_key}'，已自动降级兼容")
            options.pop(bad_key)


def run_app() -> None:
    server = run_server(8765)
    try:
        import webview
    except Exception:
        print("验证通过，且已预加载全部数据。未安装 pywebview；可直接打开 http://localhost:8765")
        try:
            while True:
                threading.Event().wait(3600)
        finally:
            server.shutdown()
        return

    icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Assets", "Sprites", "Sprites", "icon.png"))
    base_url = "http://localhost:8765"

    def wait_http_ready(timeout_seconds: float = 8.0) -> None:
        deadline = time.time() + timeout_seconds
        last_error = None
        while time.time() < deadline:
            try:
                with urlopen(f"{base_url}/api/preload_status", timeout=0.8) as resp:
                    if resp.status == 200:
                        return
            except Exception as exc:
                last_error = exc
                time.sleep(0.12)
        raise RuntimeError(f"PlanetInfo 本地服务启动失败：{last_error}")

    loading_window = None

    def bootstrap():
        wait_http_ready(15.0)
        AppHTTP.service.ensure_preload_started()
        while not AppHTTP.service.preloaded:
            time.sleep(0.2)

        def open_main_window() -> None:
            nonlocal loading_window
            main_window = create_window_compat(
                webview,
                "Weathering PlanetInfo",
                f"{base_url}/?ready=1",
                width=1220,
                height=780,
                resizable=True,
                icon=icon_path,
            )
            try:
                if loading_window is not None and hasattr(loading_window, "hide"):
                    loading_window.hide()
                elif loading_window is not None and os.name != "nt":
                    loading_window.destroy()
            except Exception as exc:
                print(f"[PlanetInfo] 关闭加载窗口时忽略异常: {exc}")
            return main_window

        open_main_window()

    try:
        loading_window = create_window_compat(
            webview,
            "Weathering PlanetInfo",
            f"{base_url}/loading",
            width=520,
            height=220,
            resizable=False,
            frameless=True,
        )
        webview.start(bootstrap, gui="edgechromium", debug=False)
    finally:
        server.shutdown()



if __name__ == "__main__":
    if not os.environ.get("DISPLAY") and os.name != "nt":
        verify_samples()
        AppHTTP.service.ensure_preload_started()
        while not AppHTTP.service.preloaded:
            time.sleep(0.2)
        print("验证通过（当前无图形环境，已预加载全部数据，跳过 Edge WebView 启动）")
    else:
        run_app()
