#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

namespace {
constexpr uint32_t MASK32 = 0xFFFFFFFFu;
constexpr int UNIVERSE_SIZE = 100;
constexpr int GALAXY_SIZE = 100;
constexpr int STAR_SYSTEM_SIZE = 32;
constexpr int MONTH_FOR_A_YEAR = 12;

struct Galaxy {
    int gx;
    int gy;
};

struct System {
    int gx;
    int gy;
    int sx;
    int sy;
    int star_type;
};

struct Planet {
    int gx;
    int gy;
    int sx;
    int sy;
    int px;
    int py;
    int star_type;
    int planet_type;
    int seconds_for_a_day;
    int days_for_a_month;
    int days_for_a_year;
    int month_for_a_year;
    int planet_size;
    int mineral_density;
};

uint32_t u32(uint64_t v) {
    return static_cast<uint32_t>(v & MASK32);
}

int32_t csharp_int32(uint64_t n) {
    uint32_t v = u32(n);
    if (v < 0x80000000u) {
        return static_cast<int32_t>(v);
    }
    return static_cast<int32_t>(static_cast<int64_t>(v) - 0x100000000LL);
}

int csharp_mod(int a, int b) {
    return a - static_cast<int>(static_cast<double>(a) / static_cast<double>(b)) * b;
}

uint32_t hash_uint(uint32_t a) {
    a = u32((a ^ 61u) ^ (a >> 16));
    a = u32(a + (a << 3));
    a = u32(a ^ (a >> 4));
    a = u32(static_cast<uint64_t>(a) * 0x27D4EB2Du);
    a = u32(a ^ (a >> 15));
    return a;
}

uint32_t hash_string(const std::string& text) {
    uint32_t result = 7;
    for (unsigned char c : text) {
        result = u32(result + c);
        result = hash_uint(result);
    }
    return result;
}

uint32_t hash_tile(int i, int j, int width, int height, int offset) {
    uint32_t raw = u32(static_cast<int64_t>(offset) * width + height + i + j * width);
    return hash_uint(raw);
}

std::string build_map_key(const std::string& map_type, int gx, int gy, int sx = -1, int sy = -1, int px = -1, int py = -1) {
    std::string out = "Weathering." + map_type + "#=" + std::to_string(gx) + "," + std::to_string(gy);
    if (sx >= 0 && sy >= 0) {
        out += "=" + std::to_string(sx) + "," + std::to_string(sy);
    }
    if (px >= 0 && py >= 0) {
        out += "=" + std::to_string(px) + "," + std::to_string(py);
    }
    return out;
}

bool is_galaxy(int gx, int gy) {
    uint32_t universe_hash = hash_string("Weathering.MapOfUniverse#");
    uint32_t tile_hash = hash_tile(gx, gy, UNIVERSE_SIZE, UNIVERSE_SIZE, csharp_int32(universe_hash));
    return tile_hash % 50u == 0u;
}

bool is_star_system(int gx, int gy, int sx, int sy) {
    std::string galaxy_map_key = build_map_key("MapOfGalaxy", gx, gy);
    uint32_t galaxy_hash = hash_string(galaxy_map_key);
    uint32_t tile_hash = hash_tile(sx, sy, GALAXY_SIZE, GALAXY_SIZE, csharp_int32(galaxy_hash));
    return tile_hash % 200u == 0u;
}

std::pair<std::pair<int, int>, std::pair<int, int>> star_positions(const std::string& star_system_map_key, bool& has_second) {
    uint32_t h = hash_string(star_system_map_key);
    int star_pos = std::abs(csharp_int32(h)) % (STAR_SYSTEM_SIZE * STAR_SYSTEM_SIZE);
    std::pair<int, int> main = {star_pos % STAR_SYSTEM_SIZE, star_pos / STAR_SYSTEM_SIZE};
    int second_pos = std::abs(csharp_int32(hash_uint(h)));
    if (second_pos == star_pos) {
        has_second = false;
        return {main, {0, 0}};
    }
    has_second = true;
    return {main, {second_pos % STAR_SYSTEM_SIZE, second_pos / STAR_SYSTEM_SIZE}};
}

int compute_star_type(const std::string& ss_map_key) {
    return static_cast<int>(hash_string(ss_map_key) % 5u);
}

bool try_compute_planet(int gx, int gy, int sx, int sy, int px, int py, int star_type, Planet& out) {
    std::string ss_map_key = build_map_key("MapOfStarSystem", gx, gy, sx, sy);
    int ss_hash_i = csharp_int32(hash_string(ss_map_key));
    uint32_t tile_hash = hash_tile(px, py, STAR_SYSTEM_SIZE, STAR_SYSTEM_SIZE, ss_hash_i);

    uint32_t h = hash_uint(tile_hash);
    h = hash_uint(h);
    if (h % 50u != 0u) {
        return false;
    }
    h = hash_uint(h);
    if (h % 2u != 0u) {
        return false;
    }

    int planet_type = -1;
    h = hash_uint(h);
    if (h % 40u == 0u) {
        planet_type = 6;  // Gaia
    } else {
        h = hash_uint(h);
        if (h % 40u == 0u) {
            planet_type = 7;  // SuperDimensional
        } else {
            h = hash_uint(h);
            if (h % 10u == 0u) {
                return false;
            }
            h = hash_uint(h);
            if (h % 9u == 0u) {
                return false;
            }
            h = hash_uint(h);
            if (h % 3u == 0u) {
                planet_type = 5;  // Continental
            } else {
                h = hash_uint(h);
                if (h % 2u == 0u) {
                    planet_type = 3;  // Molten
                } else {
                    h = hash_uint(h);
                    if (h % 4u == 0u) {
                        planet_type = 0;  // Barren
                    } else {
                        h = hash_uint(h);
                        if (h % 3u == 0u) {
                            planet_type = 1;  // Arid
                        } else {
                            h = hash_uint(h);
                            planet_type = (h % 2u == 0u) ? 4 : 2;  // Frozen : Ocean
                        }
                    }
                }
            }
        }
    }

    if (planet_type < 0) {
        return false;
    }

    std::string map_key = build_map_key("MapOfPlanet", gx, gy, sx, sy, px, py);
    std::string map_self_index = "#=" + std::to_string(gx) + "," + std::to_string(gy) + "=" + std::to_string(sx) + "," + std::to_string(sy) + "=" + std::to_string(px) + "," + std::to_string(py);

    uint32_t again = hash_uint(hash_uint(tile_hash));
    int slowed = 1 + std::abs(csharp_mod(csharp_int32(again), 7));
    uint32_t planet_hash = hash_string(map_key);
    uint32_t self_hash = hash_string(map_self_index);
    int days_per_month = 2 + static_cast<int>(planet_hash % 15u);

    out = Planet{
        gx,
        gy,
        sx,
        sy,
        px,
        py,
        star_type,
        planet_type,
        (60 * 8) / (1 + slowed),
        days_per_month,
        MONTH_FOR_A_YEAR * days_per_month,
        MONTH_FOR_A_YEAR,
        50 + static_cast<int>(self_hash % 100u),
        3 + static_cast<int>(hash_uint(u32(self_hash + 2641779086u)) % 27u),
    };
    return true;
}

void write_output(
    const std::string& path,
    const std::vector<Galaxy>& galaxies,
    const std::vector<System>& systems,
    const std::vector<Planet>& planets
) {
    std::ofstream out(path, std::ios::out | std::ios::trunc);
    out << "[GAL]" << '\n';
    for (const auto& g : galaxies) {
        out << g.gx << ',' << g.gy << '\n';
    }
    out << "[SYS]" << '\n';
    for (const auto& s : systems) {
        out << s.gx << ',' << s.gy << ',' << s.sx << ',' << s.sy << ',' << s.star_type << '\n';
    }
    out << "[PLN]" << '\n';
    for (const auto& p : planets) {
        out << p.gx << ',' << p.gy << ',' << p.sx << ',' << p.sy << ',' << p.px << ',' << p.py << ',' << p.star_type << ',' << p.planet_type
            << ',' << p.seconds_for_a_day << ',' << p.days_for_a_month << ',' << p.days_for_a_year << ',' << p.month_for_a_year
            << ',' << p.planet_size << ',' << p.mineral_density << '\n';
    }
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "usage: native_loader <output_file> <threads>" << std::endl;
        return 2;
    }

    std::string output_file = argv[1];
    int thread_count = std::max(1, std::stoi(argv[2]));
    std::atomic<int> next_row{0};
    std::atomic<int> rows_done{0};

    std::mutex merge_mutex;
    std::mutex print_mutex;
    std::vector<Galaxy> galaxies;
    std::vector<System> systems;
    std::vector<Planet> planets;

    auto worker = [&]() {
        std::vector<Galaxy> local_g;
        std::vector<System> local_s;
        std::vector<Planet> local_p;

        while (true) {
            int gy = next_row.fetch_add(1);
            if (gy >= UNIVERSE_SIZE) {
                break;
            }

            for (int gx = 0; gx < UNIVERSE_SIZE; ++gx) {
                if (!is_galaxy(gx, gy)) {
                    continue;
                }
                local_g.push_back(Galaxy{gx, gy});

                for (int sy = 0; sy < GALAXY_SIZE; ++sy) {
                    for (int sx = 0; sx < GALAXY_SIZE; ++sx) {
                        if (!is_star_system(gx, gy, sx, sy)) {
                            continue;
                        }

                        std::string ss_map_key = build_map_key("MapOfStarSystem", gx, gy, sx, sy);
                        int star_type = compute_star_type(ss_map_key);
                        local_s.push_back(System{gx, gy, sx, sy, star_type});

                        bool has_second = false;
                        auto stars = star_positions(ss_map_key, has_second);
                        auto main_star = stars.first;
                        auto second_star = stars.second;

                        for (int py = 0; py < STAR_SYSTEM_SIZE; ++py) {
                            for (int px = 0; px < STAR_SYSTEM_SIZE; ++px) {
                                bool is_star_tile = (px == main_star.first && py == main_star.second)
                                    || (has_second && px == second_star.first && py == second_star.second);
                                if (is_star_tile) {
                                    continue;
                                }
                                Planet p{};
                                if (try_compute_planet(gx, gy, sx, sy, px, py, star_type, p)) {
                                    local_p.push_back(p);
                                }
                            }
                        }
                    }
                }
            }

            int done = rows_done.fetch_add(1) + 1;
            if (done % 5 == 0 || done == UNIVERSE_SIZE) {
                std::lock_guard<std::mutex> lock(print_mutex);
                std::cout << "PROGRESS\t" << done << '\t' << UNIVERSE_SIZE << '\t' << local_g.size() << '\t' << local_s.size() << '\t' << local_p.size() << std::endl;
            }
        }

        {
            std::lock_guard<std::mutex> lock(merge_mutex);
            galaxies.insert(galaxies.end(), local_g.begin(), local_g.end());
            systems.insert(systems.end(), local_s.begin(), local_s.end());
            planets.insert(planets.end(), local_p.begin(), local_p.end());
        }
    };

    std::vector<std::thread> workers;
    workers.reserve(thread_count);
    auto begin = std::chrono::steady_clock::now();
    for (int i = 0; i < thread_count; ++i) {
        workers.emplace_back(worker);
    }
    for (auto& t : workers) {
        t.join();
    }

    std::sort(galaxies.begin(), galaxies.end(), [](const Galaxy& a, const Galaxy& b) {
        return a.gx == b.gx ? a.gy < b.gy : a.gx < b.gx;
    });
    std::sort(systems.begin(), systems.end(), [](const System& a, const System& b) {
        if (a.gx != b.gx) return a.gx < b.gx;
        if (a.gy != b.gy) return a.gy < b.gy;
        if (a.sx != b.sx) return a.sx < b.sx;
        return a.sy < b.sy;
    });

    write_output(output_file, galaxies, systems, planets);

    auto end = std::chrono::steady_clock::now();
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(end - begin).count();
    std::cout << "DONE\t" << galaxies.size() << '\t' << systems.size() << '\t' << planets.size() << '\t' << ms << std::endl;
    return 0;
}
