from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qs, unquote

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
        self.planets_cache: Dict[str, PlanetRecord] = {}

    def galaxies(self) -> List[Dict[str, int]]:
        result: List[Dict[str, int]] = []
        for gy in range(UNIVERSE_SIZE):
            for gx in range(UNIVERSE_SIZE):
                if is_galaxy((gx, gy)):
                    result.append({"x": gx, "y": gy})
        return result

    def star_systems(self, gx: int, gy: int) -> List[Dict[str, object]]:
        out: List[Dict[str, object]] = []
        for sy in range(GALAXY_SIZE):
            for sx in range(GALAXY_SIZE):
                if is_star_system((gx, gy), (sx, sy)):
                    map_key = build_map_key("MapOfStarSystem", [(gx, gy), (sx, sy)])
                    out.append({"x": sx, "y": sy, "star_type": calculate_star_type(map_key)})
        return out

    def planets(self, gx: int, gy: int, sx: int, sy: int) -> List[Dict[str, object]]:
        out: List[Dict[str, object]] = []
        for py in range(STAR_SYSTEM_SIZE):
            for px in range(STAR_SYSTEM_SIZE):
                key = build_map_key("MapOfPlanet", [(gx, gy), (sx, sy), (px, py)])
                try:
                    p = compute_planet_record(key)
                except ValueError:
                    continue
                self.planets_cache[p.map_key] = p
                out.append(asdict(p))
        return out

    def find_planet(self, map_key: str) -> Dict[str, object]:
        if map_key in self.planets_cache:
            return asdict(self.planets_cache[map_key])
        p = compute_planet_record(map_key)
        self.planets_cache[p.map_key] = p
        return asdict(p)

    def query_loaded(self, q: str, planet_type: str, sort_by: str, page: int, page_size: int) -> Dict[str, object]:
        rows = list(self.planets_cache.values())
        if q:
            rows = [x for x in rows if q in x.map_key or q in x.star_type or q in x.planet_type]
        if planet_type and planet_type != "全部":
            rows = [x for x in rows if x.planet_type == planet_type]
        if sort_by in PlanetRecord.__annotations__:
            rows.sort(key=lambda r: getattr(r, sort_by), reverse=True)

        total = len(rows)
        start = max((page - 1) * page_size, 0)
        end = start + page_size
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "rows": [asdict(x) for x in rows[start:end]],
        }

    def stats(self) -> Dict[str, int]:
        return {
            "cached_planets": len(self.planets_cache),
            "cached_star_systems": len({(p.galaxy_x, p.galaxy_y, p.star_system_x, p.star_system_y) for p in self.planets_cache.values()}),
            "cached_galaxies": len({(p.galaxy_x, p.galaxy_y) for p in self.planets_cache.values()}),
        }


HTML = """<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Weathering Universe Explorer</title>
  <script type=\"module\" src=\"https://unpkg.com/@fluentui/web-components@2.6.1/dist/web-components.min.js\"></script>
  <style>
    :root { --bg:#0b1220; --panel:#111827; --line:#334155; --txt:#e2e8f0; --sub:#93c5fd; }
    body { margin:0; background:var(--bg); color:var(--txt); font-family:Segoe UI,system-ui,sans-serif; }
    .app { display:grid; grid-template-columns: 360px 1fr; height:100vh; }
    .left { border-right:1px solid var(--line); overflow:auto; padding:10px; background:#0f172a; }
    .right { display:grid; grid-template-rows:auto auto auto 1fr; gap:8px; padding:10px; }
    .card { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:10px; }
    .row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
    .title { color:var(--sub); font-weight:700; margin:0 0 8px 0; }
    .node { padding:4px 0 4px 10px; border-radius:6px; cursor:pointer; }
    .node:hover { background:#1e293b; }
    .sub { margin-left:14px; display:none; }
    .hint { font-size:12px; color:#9ca3af; }
    table { width:100%; border-collapse:collapse; font-size:12px; }
    th, td { border:1px solid var(--line); padding:5px; }
    th { background:#1f2937; position:sticky; top:0; cursor:pointer; }
    .table-wrap { overflow:auto; max-height:100%; }
    .badge { background:#1e293b; border:1px solid var(--line); padding:4px 8px; border-radius:999px; font-size:12px; }
  </style>
</head>
<body>
<div class=\"app\">
  <aside class=\"left\">
    <div class=\"card\">
      <h3 class=\"title\">宇宙树状导航</h3>
      <div class=\"hint\">懒加载：点开星系后加载恒星系，点开恒星系后加载行星。</div>
    </div>
    <div id=\"tree\" class=\"card\" style=\"margin-top:8px\"></div>
  </aside>

  <main class=\"right\">
    <section class=\"card\">
      <h3 class=\"title\">快速定位</h3>
      <div class=\"row\">
        <fluent-text-field id=\"mapKey\" style=\"width:460px\" placeholder=\"Weathering.MapOfPlanet#=gX,gY=sX,sY=pX,pY\"></fluent-text-field>
        <fluent-button id=\"findByMapKey\" appearance=\"accent\">按 MapKey 定位</fluent-button>
      </div>
    </section>

    <section class=\"card\">
      <h3 class=\"title\">筛选器（基于已加载数据）</h3>
      <div class=\"row\">
        <fluent-text-field id=\"q\" placeholder=\"关键词\"></fluent-text-field>
        <fluent-select id=\"ptype\"><fluent-option>全部</fluent-option></fluent-select>
        <fluent-select id=\"sort\">
          <fluent-option value=\"planet_size\">planet_size</fluent-option>
          <fluent-option value=\"mineral_density\">mineral_density</fluent-option>
          <fluent-option value=\"seconds_for_a_day\">seconds_for_a_day</fluent-option>
          <fluent-option value=\"days_for_a_year\">days_for_a_year</fluent-option>
          <fluent-option value=\"galaxy_x\">galaxy_x</fluent-option>
          <fluent-option value=\"star_system_x\">star_system_x</fluent-option>
        </fluent-select>
        <fluent-button id=\"apply\">应用</fluent-button>
        <span class=\"badge\" id=\"stats\">缓存: 0</span>
      </div>
    </section>

    <section class=\"card\" id=\"detail\">请选择行星查看详情。</section>

    <section class=\"card table-wrap\">
      <table id=\"tbl\"></table>
    </section>
  </main>
</div>

<script>
const API = '/api';
const tree = document.getElementById('tree');
const tbl = document.getElementById('tbl');
const detail = document.getElementById('detail');
const stats = document.getElementById('stats');
const ptype = document.getElementById('ptype');
const mapKey = document.getElementById('mapKey');

for (const p of ["荒芜行星","干旱行星","海洋行星","熔岩行星","冰冻星球","类地行星","盖亚行星","超维星球"]) {
  const opt = document.createElement('fluent-option');
  opt.textContent = p;
  ptype.appendChild(opt);
}

let currentRows = [];
let currentSort = 'planet_size';
let sortDesc = true;

async function getJson(url){
  const r = await fetch(url);
  if(!r.ok){ throw new Error(await r.text()); }
  return await r.json();
}

function renderDetail(p){
  detail.innerHTML = `<b>MapKey:</b> ${p.map_key}<br>`+
    `<b>坐标:</b> 星系(${p.galaxy_x},${p.galaxy_y}) / 恒星系(${p.star_system_x},${p.star_system_y}) / 星球(${p.planet_x},${p.planet_y})<br>`+
    `<b>类型:</b> ${p.planet_type} / ${p.star_type}<br>`+
    `<b>昼夜:</b> ${p.seconds_for_a_day}s  <b>四季:</b> ${p.days_for_a_year}天  <b>月相:</b> ${p.days_for_a_month}天  <b>四季月相:</b> ${p.month_for_a_year}<br>`+
    `<b>大小:</b> ${p.planet_size}  <b>矿物稀疏度:</b> ${p.mineral_density}`;
}

function renderTable(rows){
  currentRows = rows.slice();
  const cols = ['galaxy_x','galaxy_y','star_system_x','star_system_y','planet_x','planet_y','planet_type','star_type','seconds_for_a_day','days_for_a_year','days_for_a_month','month_for_a_year','planet_size','mineral_density','map_key'];

  const sorted = rows.slice().sort((a,b)=>{
    if (a[currentSort] === b[currentSort]) return 0;
    return sortDesc ? (a[currentSort] > b[currentSort] ? -1 : 1) : (a[currentSort] > b[currentSort] ? 1 : -1);
  });

  const thead = '<thead><tr>'+cols.map(c=>`<th data-k="${c}">${c}${currentSort===c?(sortDesc?'▼':'▲'):''}</th>`).join('')+'</tr></thead>';
  const tbody = '<tbody>'+sorted.map(r=>'<tr>'+cols.map(c=>`<td>${r[c]}</td>`).join('')+'</tr>').join('')+'</tbody>';
  tbl.innerHTML = thead + tbody;

  for (const th of tbl.querySelectorAll('th')) {
    th.onclick = ()=>{
      const k = th.getAttribute('data-k');
      if (currentSort === k) sortDesc = !sortDesc; else { currentSort = k; sortDesc = true; }
      renderTable(currentRows);
    }
  }
}

async function refreshStats(){
  const s = await getJson(`${API}/stats`);
  stats.textContent = `缓存行星 ${s.cached_planets} | 恒星系 ${s.cached_star_systems} | 星系 ${s.cached_galaxies}`;
}

async function loadQuery(){
  const q = encodeURIComponent(document.getElementById('q').value || '');
  const pt = encodeURIComponent(ptype.value || '全部');
  const sortBy = encodeURIComponent(document.getElementById('sort').value || 'planet_size');
  const data = await getJson(`${API}/query?q=${q}&planet_type=${pt}&sort_by=${sortBy}&page=1&page_size=3000`);
  renderTable(data.rows);
  await refreshStats();
}

async function buildTree(){
  tree.innerHTML = '<div class="hint">加载星系列表中...</div>';
  const galaxies = await getJson(`${API}/galaxies`);
  tree.innerHTML = '';

  for (const g of galaxies){
    const gNode = document.createElement('div');
    gNode.className='node';
    gNode.textContent=`星系 ${g.x},${g.y}`;

    const gSub = document.createElement('div');
    gSub.className='sub';
    gSub.dataset.loaded = '0';

    gNode.onclick = async ()=>{
      if (gSub.dataset.loaded === '0'){
        gSub.innerHTML = '<div class="hint">加载恒星系...</div>';
        const systems = await getJson(`${API}/systems?gx=${g.x}&gy=${g.y}`);
        gSub.innerHTML = '';
        for (const s of systems){
          const sNode = document.createElement('div');
          sNode.className='node';
          sNode.textContent=`恒星系 ${s.x},${s.y} (${s.star_type})`;

          const sSub = document.createElement('div');
          sSub.className='sub';
          sSub.dataset.loaded='0';

          sNode.onclick = async (ev)=>{
            ev.stopPropagation();
            if (sSub.dataset.loaded === '0'){
              sSub.innerHTML = '<div class="hint">加载行星...</div>';
              const planets = await getJson(`${API}/planets?gx=${g.x}&gy=${g.y}&sx=${s.x}&sy=${s.y}`);
              sSub.innerHTML = '';
              for (const p of planets){
                const pNode = document.createElement('div');
                pNode.className='node';
                pNode.textContent=`星球 ${p.planet_x},${p.planet_y} ${p.planet_type}`;
                pNode.onclick = (e)=>{ e.stopPropagation(); renderDetail(p); };
                sSub.appendChild(pNode);
              }
              sSub.dataset.loaded='1';
              await loadQuery();
            }
            sSub.style.display = sSub.style.display === 'none' ? 'block' : 'none';
          };

          gSub.appendChild(sNode);
          gSub.appendChild(sSub);
        }
        gSub.dataset.loaded = '1';
      }
      gSub.style.display = gSub.style.display === 'none' ? 'block' : 'none';
    };

    tree.appendChild(gNode);
    tree.appendChild(gSub);
  }

  await refreshStats();
}

document.getElementById('apply').onclick = loadQuery;
document.getElementById('findByMapKey').onclick = async ()=>{
  try {
    const k = encodeURIComponent(mapKey.value.trim());
    const p = await getJson(`${API}/planet?map_key=${k}`);
    renderDetail(p);
    await loadQuery();
  } catch (e){
    detail.textContent = '定位失败: ' + e;
  }
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
                self._html(HTML)
                return
            if path == "/api/galaxies":
                self._json(self.service.galaxies())
                return
            if path == "/api/systems":
                self._json(self.service.star_systems(int(params["gx"]), int(params["gy"])))
                return
            if path == "/api/planets":
                self._json(self.service.planets(int(params["gx"]), int(params["gy"]), int(params["sx"]), int(params["sy"])))
                return
            if path == "/api/planet":
                self._json(self.service.find_planet(params["map_key"]))
                return
            if path == "/api/query":
                self._json(
                    self.service.query_loaded(
                        params.get("q", ""),
                        params.get("planet_type", "全部"),
                        params.get("sort_by", "planet_size"),
                        int(params.get("page", "1")),
                        int(params.get("page_size", "1000")),
                    )
                )
                return
            if path == "/api/stats":
                self._json(self.service.stats())
                return
            self._json({"error": "not found"}, status=404)
        except Exception as e:
            self._json({"error": str(e)}, status=400)


def run_server(port: int = 8765) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", port), AppHTTP)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


def run_app() -> None:
    verify_samples()
    server = run_server(8765)
    try:
        import webview
    except Exception:
        print("验证通过，但未安装 pywebview；可直接打开 http://127.0.0.1:8765")
        try:
            while True:
                threading.Event().wait(3600)
        finally:
            server.shutdown()
        return

    try:
        webview.create_window("Weathering Universe Explorer", "http://127.0.0.1:8765", width=1500, height=920)
        webview.start(gui="edgechromium", debug=False)
    finally:
        server.shutdown()


if __name__ == "__main__":
    if not os.environ.get("DISPLAY") and os.name != "nt":
        verify_samples()
        print("验证通过（当前无图形环境，跳过 Edge WebView 启动）")
    else:
        run_app()
