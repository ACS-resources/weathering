package com.weathering.generation;

import java.util.EnumMap;
import java.util.Map;

public final class GenerationParityTest {
    public static void main(String[] args) {
        testUniverseAndGalaxyDensity();
        testStarSystemClassification();
        testPlanetProfileAndTerrain();
        testStartingPlanetKeyGeneration();
        System.out.println("All generation parity checks passed.");
    }

    private static void testUniverseAndGalaxyDensity() {
        int width = 100;
        int height = 100;
        int mapHash = 123456789;
        int galaxyCount = 0;
        int starSystemCount = 0;
        for (int i = 0; i < width; i++) {
            for (int j = 0; j < height; j++) {
                long tileHash = Hashing.hash(i, j, width, height, mapHash);
                if (CelestialGeneration.isGalaxyTile(tileHash)) galaxyCount++;
                if (CelestialGeneration.isStarSystemTile(tileHash)) starSystemCount++;
            }
        }
        require(galaxyCount > 0, "Galaxy generation should produce non-zero galaxies");
        require(starSystemCount > 0, "Star-system generation should produce non-zero systems");
    }

    private static void testStarSystemClassification() {
        long mapHash = 3141592653L;
        var stars = CelestialGeneration.computeStarPositions(mapHash);
        require(stars.x() >= 0 && stars.x() < 32, "Primary star x out of range");
        require(stars.y() >= 0 && stars.y() < 32, "Primary star y out of range");

        int width = 32;
        int height = 32;
        Map<CelestialGeneration.BodyType, Integer> histogram = new EnumMap<>(CelestialGeneration.BodyType.class);
        for (int i = 0; i < width; i++) {
            for (int j = 0; j < height; j++) {
                long tileHash = Hashing.hash(i, j, width, height, (int) mapHash);
                var body = CelestialGeneration.classifyBody(tileHash, mapHash, i, j, stars);
                histogram.put(body, histogram.getOrDefault(body, 0) + 1);
            }
        }
        require(histogram.values().stream().mapToInt(Integer::intValue).sum() == 1024, "Body classification count mismatch");
        require(histogram.keySet().stream().anyMatch(k -> k.name().startsWith("Star")), "Expected star body in star system");
        require(histogram.containsKey(CelestialGeneration.BodyType.SpaceEmptiness), "Expected space emptiness to dominate");
    }

    private static void testPlanetProfileAndTerrain() {
        long mapHash = 99887766L;
        long selfMapHash = 1234567890L;
        var profile = PlanetGeneration.profile(mapHash, selfMapHash);
        require(profile.size() == 50 + (int) (selfMapHash % 100), "Planet size formula mismatch");
        require(profile.mineralDensity() >= 3 && profile.mineralDensity() <= 29, "Mineral density range mismatch");

        var map = PlanetGeneration.generate(mapHash, selfMapHash, 5);
        require(map.width() == profile.size(), "Generated width mismatch");
        require(map.height() == profile.size(), "Generated height mismatch");

        int sea = 0, plain = 0, forest = 0, mountain = 0;
        for (int i = 0; i < map.width(); i++) {
            for (int j = 0; j < map.height(); j++) {
                switch (map.terrainTypes()[i][j]) {
                    case TerrainType_Sea -> sea++;
                    case TerrainType_Plain -> plain++;
                    case TerrainType_Forest -> forest++;
                    case TerrainType_Mountain -> mountain++;
                }
            }
        }
        require(sea + plain + forest + mountain == map.width() * map.height(), "Terrain coverage mismatch");
        require(sea > 0 && plain > 0 && mountain > 0, "Terrain mix should include sea/plain/mountain");
    }


    private static void testStartingPlanetKeyGeneration() {
        String mapKey = "Weathering.MapOfPlanet#=1,4=14,93=24,31";
        String selfIndex = mapKey.substring(mapKey.indexOf('#'));

        long mapHash = Hashing.hashString(mapKey);
        long selfMapHash = Hashing.hashString(selfIndex);
        var map = PlanetGeneration.generate(mapHash, selfMapHash, 5);

        require(map.width() >= 64 && map.height() >= 64, "Starting planet map should be large enough for a 64x64 sample");

        int terrainCount = 0;
        for (int x = 0; x < 64; x++) {
            for (int y = 0; y < 64; y++) {
                var terrain = map.terrainTypes()[x][y];
                require(terrain != null, "Terrain value should never be null");
                terrainCount++;
            }
        }
        require(terrainCount == 4096, "64x64 starting-star terrain sample size mismatch");
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalStateException(message);
    }
}
