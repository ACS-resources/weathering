from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

MASK32 = 0xFFFFFFFF
UNIVERSE_WIDTH = 100
UNIVERSE_HEIGHT = 100
GALAXY_WIDTH = 100
GALAXY_HEIGHT = 100
STAR_SYSTEM_WIDTH = 32
STAR_SYSTEM_HEIGHT = 32
STAR_SYSTEM_DENSITY = 200


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


STAR_TYPES = {
    0: "蓝色恒星",
    1: "白色恒星",
    2: "黄色恒星",
    3: "橙色恒星",
    4: "红色恒星",
}

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

PLANET_TEXTURES = {
    "PlanetBarren": "PlanetBarren.png",
    "PlanetArid": "PlanetArid.png",
    "PlanetOcean": "PlanetOcean.png",
    "PlanetMolten": "PlanetMolten.png",
    "PlanetFrozen": "PlanetFrozen.png",
    "PlanetContinental": "PlanetContinental.png",
    "PlanetGaia": "PlanetGaia.png",
    "PlanetSuperDimensional": "PlanetSuperDimensional.png",
}

TERRESTRIAL_TYPES = {
    "PlanetBarren",
    "PlanetArid",
    "PlanetOcean",
    "PlanetMolten",
    "PlanetFrozen",
    "PlanetContinental",
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


@dataclass(frozen=True)
class PlanetRecord:
    map_key: str
    galaxy_pos: Tuple[int, int]
    star_system_pos: Tuple[int, int]
    planet_pos: Tuple[int, int]
    star_type: str
    planet_type: str
    planet_type_key: str
    seconds_for_a_day: int
    days_for_a_month: int
    days_for_a_year: int
    month_for_a_year: int
    planet_size: int
    mineral_density: int


def parse_map_key(map_key: str) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
    if "#" not in map_key:
        raise ValueError(map_key)
    _, index = map_key.split("#", 1)
    coords = [p for p in index.split("=") if p]
    if len(coords) != 3:
        raise ValueError(f"Expect 3 levels for MapOfPlanet, got {len(coords)} in {map_key}")
    parsed: List[Tuple[int, int]] = []
    for c in coords:
        x, y = c.split(",")
        parsed.append((int(x), int(y)))
    return parsed[0], parsed[1], parsed[2]


def build_map_key(map_type: str, coords: Iterable[Tuple[int, int]]) -> str:
    suffix = "".join(f"={x},{y}" for x, y in coords)
    return f"Weathering.{map_type}#{suffix}"


def slice_self_map_key_index(map_key: str) -> str:
    idx = map_key.index("#")
    return map_key[idx:]


def calculate_celestial_body_type(star_system_map_key: str, planet_pos: Tuple[int, int]) -> str:
    star_system_hash = HashUtility.hash_string(star_system_map_key)
    star_pos = abs(csharp_int32(star_system_hash)) % (STAR_SYSTEM_HEIGHT * STAR_SYSTEM_HEIGHT)
    star_x = star_pos % STAR_SYSTEM_WIDTH
    star_y = star_pos // STAR_SYSTEM_HEIGHT

    tile_hash = HashUtility.hash_tile(
        planet_pos[0],
        planet_pos[1],
        STAR_SYSTEM_WIDTH,
        STAR_SYSTEM_HEIGHT,
        csharp_int32(star_system_hash),
    )

    hashcode = HashUtility.hash_uint(tile_hash)
    is_star = star_x == planet_pos[0] and star_y == planet_pos[1]
    if is_star:
        return "Star"

    hashcode, v = HashUtility.hashed_ref(hashcode)
    if v % 50 != 0:
        return "SpaceEmptiness"

    hashcode, v = HashUtility.hashed_ref(hashcode)
    if v % 2 != 0:
        return "Asteroid"

    hashcode, v = HashUtility.hashed_ref(hashcode)
    if v % 40 == 0:
        return "PlanetGaia"

    hashcode, v = HashUtility.hashed_ref(hashcode)
    if v % 40 == 0:
        return "PlanetSuperDimensional"

    hashcode, v = HashUtility.hashed_ref(hashcode)
    if v % 10 == 0:
        return "GasGiant"

    hashcode, v = HashUtility.hashed_ref(hashcode)
    if v % 9 == 0:
        return "GasGiantRinged"

    hashcode, v = HashUtility.hashed_ref(hashcode)
    if v % 3 == 0:
        return "PlanetContinental"

    hashcode, v = HashUtility.hashed_ref(hashcode)
    if v % 2 == 0:
        return "PlanetMolten"

    hashcode, v = HashUtility.hashed_ref(hashcode)
    if v % 4 == 0:
        return "PlanetBarren"

    hashcode, v = HashUtility.hashed_ref(hashcode)
    if v % 3 == 0:
        return "PlanetArid"

    hashcode, v = HashUtility.hashed_ref(hashcode)
    if v % 2 == 0:
        return "PlanetFrozen"

    return "PlanetOcean"


def calculate_star_type(star_system_map_key: str) -> str:
    star_hashcode = HashUtility.hash_string(slice_self_map_key_index(star_system_map_key))
    return STAR_TYPES[star_hashcode % 5]


def compute_planet_record(planet_map_key: str) -> PlanetRecord:
    g_pos, s_pos, p_pos = parse_map_key(planet_map_key)

    star_system_map_key = build_map_key("MapOfStarSystem", [g_pos, s_pos])
    planet_type_key = calculate_celestial_body_type(star_system_map_key, p_pos)

    if planet_type_key not in TERRESTRIAL_TYPES:
        raise ValueError(f"{planet_map_key} is not an open terrestrial planet, got {planet_type_key}")

    star_system_hash = HashUtility.hash_string(star_system_map_key)
    tile_hash = HashUtility.hash_tile(p_pos[0], p_pos[1], STAR_SYSTEM_WIDTH, STAR_SYSTEM_HEIGHT, csharp_int32(star_system_hash))

    again = HashUtility.hash_uint(tile_hash)
    again = HashUtility.hash_uint(again)
    slowed_animation = 1 + abs(csharp_mod(csharp_int32(again), 7))
    seconds_for_a_day = (60 * 8) // (1 + slowed_animation)

    planet_map_hash = HashUtility.hash_string(planet_map_key)
    child_index_hash = HashUtility.hash_string(slice_self_map_key_index(planet_map_key))
    days_for_a_month = 2 + (planet_map_hash % 15)
    month_for_a_year = 12
    days_for_a_year = month_for_a_year * days_for_a_month
    planet_size = 50 + (child_index_hash % 100)
    mineral_density = 3 + (HashUtility.add_salt(child_index_hash, 2641779086) % 27)

    return PlanetRecord(
        map_key=planet_map_key,
        galaxy_pos=g_pos,
        star_system_pos=s_pos,
        planet_pos=p_pos,
        star_type=calculate_star_type(star_system_map_key),
        planet_type=PLANET_TYPES[planet_type_key],
        planet_type_key=planet_type_key,
        seconds_for_a_day=seconds_for_a_day,
        days_for_a_month=days_for_a_month,
        days_for_a_year=days_for_a_year,
        month_for_a_year=month_for_a_year,
        planet_size=planet_size,
        mineral_density=mineral_density,
    )


def iter_galaxies() -> Iterator[GalaxyRecord]:
    for y in range(UNIVERSE_HEIGHT):
        for x in range(UNIVERSE_WIDTH):
            yield GalaxyRecord((x, y), build_map_key("MapOfGalaxy", [(x, y)]))


def iter_star_systems(galaxy_pos: Tuple[int, int]) -> Iterator[StarSystemRecord]:
    galaxy_hash = HashUtility.hash_string(build_map_key("MapOfGalaxy", [galaxy_pos]))
    for y in range(GALAXY_HEIGHT):
        for x in range(GALAXY_WIDTH):
            tile_hash = HashUtility.hash_tile(x, y, GALAXY_WIDTH, GALAXY_HEIGHT, csharp_int32(galaxy_hash))
            if tile_hash % STAR_SYSTEM_DENSITY == 0:
                m = build_map_key("MapOfStarSystem", [galaxy_pos, (x, y)])
                yield StarSystemRecord(galaxy_pos, (x, y), m, calculate_star_type(m))


def iter_planets(star_system: StarSystemRecord, only_terrestrial: bool = True) -> Iterator[PlanetRecord]:
    for y in range(STAR_SYSTEM_HEIGHT):
        for x in range(STAR_SYSTEM_WIDTH):
            key = build_map_key("MapOfPlanet", [star_system.galaxy_pos, star_system.pos, (x, y)])
            try:
                rec = compute_planet_record(key)
                yield rec
            except ValueError:
                if not only_terrestrial:
                    continue
                continue


def sort_planets(planets: List[PlanetRecord], by: str, reverse: bool = False) -> List[PlanetRecord]:
    return sorted(planets, key=lambda x: getattr(x, by), reverse=reverse)


def filter_planets(
    planets: Iterable[PlanetRecord],
    planet_type: Optional[str] = None,
    star_type: Optional[str] = None,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    min_mineral: Optional[int] = None,
    max_mineral: Optional[int] = None,
) -> List[PlanetRecord]:
    result: List[PlanetRecord] = []
    for p in planets:
        if planet_type and p.planet_type != planet_type:
            continue
        if star_type and p.star_type != star_type:
            continue
        if min_size is not None and p.planet_size < min_size:
            continue
        if max_size is not None and p.planet_size > max_size:
            continue
        if min_mineral is not None and p.mineral_density < min_mineral:
            continue
        if max_mineral is not None and p.mineral_density > max_mineral:
            continue
        result.append(p)
    return result


def export_planet_preview(record: PlanetRecord, output: Path) -> Path:
    root = Path(__file__).resolve().parents[1]
    texture_name = PLANET_TEXTURES[record.planet_type_key]
    src = root / "Assets" / "Tiles" / "CelestialBodies" / texture_name
    if not src.exists():
        raise FileNotFoundError(src)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(src.read_bytes())
    return output


if __name__ == "__main__":
    samples = [
        "Weathering.MapOfPlanet#=1,4=14,93=24,31",
        "Weathering.MapOfPlanet#=1,4=14,93=24,1",
        "Weathering.MapOfPlanet#=97,11=18,1=20,6",
    ]
    records = [compute_planet_record(k) for k in samples]
    for r in sort_planets(records, by="planet_size", reverse=True):
        print(r)
