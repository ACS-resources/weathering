from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

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


class UniverseService:
    def __init__(self) -> None:
        self.planet_cache: Dict[str, PlanetRecord] = {}

    def galaxies(self) -> List[Dict[str, int]]:
        out: List[Dict[str, int]] = []
        for y in range(UNIVERSE_SIZE):
            for x in range(UNIVERSE_SIZE):
                if is_galaxy((x, y)):
                    out.append({"x": x, "y": y})
        return out

    def star_systems(self, gx: int, gy: int) -> List[Dict[str, object]]:
        out: List[Dict[str, object]] = []
        for y in range(GALAXY_SIZE):
            for x in range(GALAXY_SIZE):
                if is_star_system((gx, gy), (x, y)):
                    key = build_map_key("MapOfStarSystem", [(gx, gy), (x, y)])
                    out.append({"x": x, "y": y, "star_type": calculate_star_type(key)})
        return out

    def planets(self, gx: int, gy: int, sx: int, sy: int) -> List[Dict[str, object]]:
        out: List[Dict[str, object]] = []
        for y in range(STAR_SYSTEM_SIZE):
            for x in range(STAR_SYSTEM_SIZE):
                key = build_map_key("MapOfPlanet", [(gx, gy), (sx, sy), (x, y)])
                try:
                    p = compute_planet_record(key)
                except ValueError:
                    continue
                self.planet_cache[key] = p
                out.append(asdict(p))
        return out

    def query_loaded(self, q: str, planet_type: str, sort_by: str) -> List[Dict[str, object]]:
        rows = list(self.planet_cache.values())
        if q:
            rows = [r for r in rows if q in r.map_key or q in r.planet_type or q in r.star_type]
        if planet_type and planet_type != "全部":
            rows = [r for r in rows if r.planet_type == planet_type]
        if hasattr(PlanetRecord, sort_by):
            rows.sort(key=lambda x: getattr(x, sort_by), reverse=True)
        return [asdict(x) for x in rows]


HTML = """<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Weathering 宇宙筛选器</title>
  <script type=\"module\" src=\"https://unpkg.com/@fluentui/web-components@2.6.1/dist/web-components.min.js\"></script>
  <style>
    body { margin:0; font-family: Segoe UI, system-ui; background:#0f172a; color:#e5e7eb; }
    .app { display:grid; grid-template-columns: 360px 1fr; height:100vh; }
    .left { border-right:1px solid #334155; overflow:auto; padding:10px; }
    .right { display:grid; grid-template-rows:auto auto 1fr; gap:8px; padding:10px; }
    .tree-node { padding:4px 0 4px 10px; cursor:pointer; }
    .tree-node:hover { background:#1e293b; }
    .tools { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
    .details { background:#111827; border:1px solid #334155; padding:10px; white-space:pre-wrap; }
    table { width:100%; border-collapse:collapse; background:#111827; border:1px solid #334155; }
    th, td { border:1px solid #334155; padding:6px; font-size:12px; }
    th { background:#1f2937; position:sticky; top:0; }
    .table-wrap { overflow:auto; }
  </style>
</head>
<body>
<div class=\"app\">
  <div class=\"left\">
    <h3>宇宙树</h3>
    <div id=\"tree\"></div>
  </div>
  <div class=\"right\">
    <div class=\"tools\">
      <fluent-text-field id=\"q\" placeholder=\"查询 mapKey/类型\"></fluent-text-field>
      <fluent-select id=\"ptype\"><fluent-option>全部</fluent-option></fluent-select>
      <fluent-select id=\"sortBy\">
        <fluent-option value=\"planet_size\">planet_size</fluent-option>
        <fluent-option value=\"mineral_density\">mineral_density</fluent-option>
        <fluent-option value=\"seconds_for_a_day\">seconds_for_a_day</fluent-option>
        <fluent-option value=\"days_for_a_year\">days_for_a_year</fluent-option>
      </fluent-select>
      <fluent-button appearance=\"accent\" id=\"apply\">应用筛选（已加载数据）</fluent-button>
    </div>
    <div class=\"details\" id=\"detail\">请选择左侧星球节点查看详情</div>
    <div class=\"table-wrap\"><table id=\"tbl\"></table></div>
  </div>
</div>
<script>
const API_BASE = '/api';
const detail = document.getElementById('detail');
const tree = document.getElementById('tree');
const tbl = document.getElementById('tbl');
const ptype = document.getElementById('ptype');

const PLANET_TYPES = ["荒芜行星","干旱行星","海洋行星","熔岩行星","冰冻星球","类地行星","盖亚行星","超维星球"];
for (const t of PLANET_TYPES){ const o=document.createElement('fluent-option'); o.textContent=t; ptype.appendChild(o); }

async function getJson(url){ return await (await fetch(url)).json(); }

function renderTable(rows){
  const columns = [
    'galaxy_x','galaxy_y','star_system_x','star_system_y','planet_x','planet_y',
    'planet_type','star_type','seconds_for_a_day','days_for_a_year','days_for_a_month','month_for_a_year',
    'planet_size','mineral_density','map_key'
  ];
  tbl.innerHTML = '<thead><tr>'+columns.map(c=>`<th>${c}</th>`).join('')+'</tr></thead>'+
    '<tbody>'+rows.map(r=>'<tr>'+columns.map(c=>`<td>${r[c]}</td>`).join('')+'</tr>').join('')+'</tbody>';
}

function showPlanet(p){
  detail.textContent = `MapKey: ${p.map_key}\n`+
    `Galaxy: (${p.galaxy_x}, ${p.galaxy_y})\nStarSystem: (${p.star_system_x}, ${p.star_system_y})\nPlanet: (${p.planet_x}, ${p.planet_y})\n`+
    `类型: ${p.planet_type} / 恒星: ${p.star_type}\n`+
    `昼夜: ${p.seconds_for_a_day}s  四季: ${p.days_for_a_year}天  月相: ${p.days_for_a_month}天  四季月相: ${p.month_for_a_year}\n`+
    `大小: ${p.planet_size}  矿物稀疏度: ${p.mineral_density}`;
}

async function buildTree(){
  const galaxies = await getJson(`${API_BASE}/galaxies`);
  for (const g of galaxies){
    const gDiv = document.createElement('div');
    gDiv.className='tree-node';
    gDiv.textContent = `星系 ${g.x},${g.y}`;
    const gChildren = document.createElement('div');
    gChildren.style.marginLeft='14px';
    gChildren.style.display='none';
    gDiv.onclick = async () => {
      if (gChildren.dataset.loaded !== '1'){
        const systems = await getJson(`${API_BASE}/systems?gx=${g.x}&gy=${g.y}`);
        for (const s of systems){
          const sDiv = document.createElement('div');
          sDiv.className='tree-node';
          sDiv.textContent = `恒星系 ${s.x},${s.y} (${s.star_type})`;
          const sChildren = document.createElement('div');
          sChildren.style.marginLeft='14px';
          sChildren.style.display='none';
          sDiv.onclick = async (ev) => {
            ev.stopPropagation();
            if (sChildren.dataset.loaded !== '1'){
              const planets = await getJson(`${API_BASE}/planets?gx=${g.x}&gy=${g.y}&sx=${s.x}&sy=${s.y}`);
              for (const p of planets){
                const pDiv = document.createElement('div');
                pDiv.className='tree-node';
                pDiv.textContent = `星球 ${p.planet_x},${p.planet_y} ${p.planet_type}`;
                pDiv.onclick = (e)=>{ e.stopPropagation(); showPlanet(p); };
                sChildren.appendChild(pDiv);
              }
              sChildren.dataset.loaded='1';
            }
            sChildren.style.display = sChildren.style.display === 'none' ? 'block' : 'none';
          };
          gChildren.appendChild(sDiv);
          gChildren.appendChild(sChildren);
        }
        gChildren.dataset.loaded='1';
      }
      gChildren.style.display = gChildren.style.display === 'none' ? 'block' : 'none';
    };
    tree.appendChild(gDiv);
    tree.appendChild(gChildren);
  }
}

document.getElementById('apply').onclick = async () => {
  const q = encodeURIComponent(document.getElementById('q').value || '');
  const type = encodeURIComponent(ptype.value || '全部');
  const sortBy = encodeURIComponent(document.getElementById('sortBy').value || 'planet_size');
  const rows = await getJson(`${API_BASE}/query?q=${q}&planet_type=${type}&sort_by=${sortBy}`);
  renderTable(rows);
};

buildTree();
</script>
</body>
</html>
"""


class AppHTTP(BaseHTTPRequestHandler):
    service: UniverseService = UniverseService()

    def _json(self, data: object, status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _html(self, html: str, status: int = 200) -> None:
        raw = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        path, _, qs = self.path.partition("?")
        params = {}
        if qs:
            for part in qs.split("&"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    params[k] = v.replace("%20", " ")

        if path == "/":
            self._html(HTML)
        elif path == "/api/galaxies":
            self._json(self.service.galaxies())
        elif path == "/api/systems":
            self._json(self.service.star_systems(int(params["gx"]), int(params["gy"])))
        elif path == "/api/planets":
            self._json(self.service.planets(int(params["gx"]), int(params["gy"]), int(params["sx"]), int(params["sy"])))
        elif path == "/api/query":
            self._json(self.service.query_loaded(params.get("q", ""), params.get("planet_type", "全部"), params.get("sort_by", "planet_size")))
        else:
            self._json({"error": "not found"}, status=404)


def run_app() -> None:
    _verify_samples()

    server = ThreadingHTTPServer(("127.0.0.1", 8765), AppHTTP)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    try:
        import webview
    except Exception:
        print("验证通过，但未安装 pywebview；请安装后使用 Edge WebView2 界面。")
        print("可临时访问: http://127.0.0.1:8765")
        t.join()
        return

    try:
        webview.create_window("Weathering 宇宙筛选器", "http://127.0.0.1:8765", width=1440, height=860)
        webview.start(gui="edgechromium", debug=False)
    finally:
        server.shutdown()


if __name__ == "__main__":
    if not os.environ.get("DISPLAY") and os.name != "nt":
        _verify_samples()
        print("验证通过（当前无图形界面环境，跳过 Edge WebView 启动）")
    else:
        run_app()
