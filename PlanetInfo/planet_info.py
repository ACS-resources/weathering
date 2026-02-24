from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Iterable


MASK32 = 0xFFFFFFFF


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


def calculate_star_type(star_system_map_key: str) -> str:
    star_hashcode = HashUtility.hash_string(slice_self_map_key_index(star_system_map_key))
    return STAR_TYPES[star_hashcode % 5]


def compute_planet_record(planet_map_key: str) -> PlanetRecord:
    g_pos, s_pos, p_pos = parse_map_key(planet_map_key)

    star_system_map_key = build_map_key("MapOfStarSystem", [g_pos, s_pos])
    star_system_hash = HashUtility.hash_string(star_system_map_key)

    # TileHashCode on MapOfStarSystem
    offset = csharp_int32(star_system_hash)
    tile_hash = HashUtility.hash_tile(p_pos[0], p_pos[1], 32, 32, offset)

    # MapOfStarSystemDefaultTile.OnEnable
    hashcode = HashUtility.hash_uint(tile_hash)
    is_star = False
    if is_star:
        celestial = "PlanetContinental"
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
                                                if v % 2 == 0:
                                                    celestial = "PlanetFrozen"
                                                else:
                                                    celestial = "PlanetOcean"

    if celestial not in PLANET_TYPES:
        raise ValueError(f"{planet_map_key} is not a playable terrestrial planet, got {celestial}")

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

    star_hashcode = HashUtility.hash_string(slice_self_map_key_index(star_system_map_key))

    return PlanetRecord(
        map_key=planet_map_key,
        galaxy_pos=g_pos,
        star_system_pos=s_pos,
        planet_pos=p_pos,
        star_type=STAR_TYPES[star_hashcode % 5],
        planet_type=PLANET_TYPES[celestial],
        seconds_for_a_day=seconds_for_a_day,
        days_for_a_month=days_for_a_month,
        days_for_a_year=days_for_a_year,
        month_for_a_year=month_for_a_year,
        planet_size=planet_size,
        mineral_density=mineral_density,
    )


def sort_planets(planets: List[PlanetRecord], by: str, reverse: bool = False) -> List[PlanetRecord]:
    return sorted(planets, key=lambda x: getattr(x, by), reverse=reverse)


def planets_in_star_system(galaxy_pos: Tuple[int, int], star_system_pos: Tuple[int, int]) -> List[PlanetRecord]:
    records: List[PlanetRecord] = []
    for y in range(32):
        for x in range(32):
            key = build_map_key("MapOfPlanet", [galaxy_pos, star_system_pos, (x, y)])
            try:
                records.append(compute_planet_record(key))
            except ValueError:
                continue
    return records


if __name__ == "__main__":
    samples = [
        "Weathering.MapOfPlanet#=1,4=14,93=24,31",
        "Weathering.MapOfPlanet#=1,4=14,93=24,1",
        "Weathering.MapOfPlanet#=97,11=18,1=20,6",
    ]
    records = [compute_planet_record(k) for k in samples]
    for r in sort_planets(records, by="planet_size", reverse=True):
        print(r)
