package com.weathering.generation;

import java.util.EnumMap;
import java.util.Map;

public final class GenerationParityTest {
    public static void main(String[] args) {
        testUniverseAndGalaxyDensity();
        testStarSystemClassification();
        testPlanetProfileAndTerrain();
        testStartingPlanetKeyGeneration();
        testKnownHierarchyCoordinates();
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

        int oresOnMountains = 0;
        for (int i = 0; i < map.width(); i++) {
            for (int j = 0; j < map.height(); j++) {
                var ore = map.oreTypes()[i][j];
                if (ore != null) {
                    require(map.terrainTypes()[i][j] == PlanetGeneration.TerrainType.TerrainType_Mountain,
                        "Ore must generate only on mountain terrain");
                    oresOnMountains++;
                }
            }
        }
        require(oresOnMountains > 0, "Expected at least one ore tile on mountains");
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
                var ore = map.oreTypes()[x][y];
                if (ore != null) {
                    require(terrain == PlanetGeneration.TerrainType.TerrainType_Mountain,
                        "Starting-planet ore must sit on mountain terrain");
                }
                terrainCount++;
            }
        }
        require(terrainCount == 4096, "64x64 starting-star terrain sample size mismatch");
    }

    private static void testKnownHierarchyCoordinates() {
        long universeHash = Hashing.hashString("Weathering.MapOfUniverse#");
        long universeTileHash = Hashing.hash(1, 4, 100, 100, (int) universeHash);
        require(CelestialGeneration.isGalaxyTile(universeTileHash), "Expected galaxy at universe (1,4)");

        long galaxyHash = Hashing.hashString("Weathering.MapOfGalaxy#=1,4");
        long galaxyTileHash = Hashing.hash(14, 93, 100, 100, (int) galaxyHash);
        require(CelestialGeneration.isStarSystemTile(galaxyTileHash), "Expected star system at galaxy (14,93)");

        long starSystemHash = Hashing.hashString("Weathering.MapOfStarSystem#=1,4=14,93");
        var stars = CelestialGeneration.computeStarPositions(starSystemHash);
        long planetTileHash = Hashing.hash(24, 31, 32, 32, (int) starSystemHash);
        var body = CelestialGeneration.classifyBody(planetTileHash, starSystemHash, 24, 31, stars);
        boolean isPlanetLike = body.name().startsWith("Planet")
            || body == CelestialGeneration.BodyType.GasGiant
            || body == CelestialGeneration.BodyType.GasGiantRinged;
        require(isPlanetLike, "Expected planet-like body at star-system tile (24,31)");

        int planetLikeBodies = 0;
        for (int y = 0; y < 32; y++) {
            for (int x = 0; x < 32; x++) {
                long tileHash = Hashing.hash(x, y, 32, 32, (int) starSystemHash);
                var classification = CelestialGeneration.classifyBody(tileHash, starSystemHash, x, y, stars);
                if (classification.name().startsWith("Planet")
                    || classification == CelestialGeneration.BodyType.GasGiant
                    || classification == CelestialGeneration.BodyType.GasGiantRinged) {
                    planetLikeBodies++;
                }
            }
        }
        require(planetLikeBodies == 16, "Expected 16 planet-like bodies in star system (1,4)->(14,93)");
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalStateException(message);
    }
}
