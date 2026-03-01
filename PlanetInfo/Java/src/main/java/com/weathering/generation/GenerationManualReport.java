package com.weathering.generation;

import java.util.EnumMap;
import java.util.Map;

/**
 * Produces human-checkable generation output for manual inspection.
 */
public final class GenerationManualReport {
    private static final String ANSI_RESET = "\u001B[0m";
    private static final String ANSI_BG_AQUA = "\u001B[48;5;45m";
    private static final String ANSI_BG_GRASS = "\u001B[48;5;82m";
    private static final String ANSI_BG_FOREST = "\u001B[48;5;22m";
    private static final String ANSI_BG_MOUNTAIN = "\u001B[48;5;94m";
    private static final String ANSI_BG_COAL = "\u001B[48;5;16m";
    private static final String ANSI_BG_IRON = "\u001B[48;5;252m";
    private static final String ANSI_BG_GOLD = "\u001B[48;5;220m";
    private static final String ANSI_BG_BAUXITE = "\u001B[48;5;137m";

    private static final String ANSI_FG_DARK = "\u001B[38;5;16m";
    private static final String ANSI_FG_LIGHT = "\u001B[38;5;255m";

    private static final String STARTING_PLANET_MAP_KEY = "Weathering.MapOfPlanet#=1,4=14,93=24,31";

    private GenerationManualReport() {}

    public static void main(String[] args) {
        long universeMapHash = 123456789L;
        long galaxyMapHash = 987654321L;
        long starSystemMapHash = 3141592653L;
        long planetMapHash = 99887766L;
        long planetSelfMapHash = 1234567890L;

        printKnownHierarchyCheck();
        printUniverseReport(universeMapHash);
        printGalaxyReport(galaxyMapHash);
        printStarSystemReport(starSystemMapHash);
        printPlanetReport(planetMapHash, planetSelfMapHash);
        printStartingStarPlanetReport(STARTING_PLANET_MAP_KEY, 64);
    }

    private static void printStartingStarPlanetReport(String mapKey, int sampleSize) {
        String selfIndex = selfMapKeyIndex(mapKey);
        long mapHash = Hashing.hashString(mapKey);
        long selfMapHash = Hashing.hashString(selfIndex);

        var profile = PlanetGeneration.profile(mapHash, selfMapHash);
        var map = PlanetGeneration.generate(mapHash, selfMapHash, 5);

        System.out.println("=== Starting Star Planet Report ===");
        System.out.printf("MapKey=%s%n", mapKey);
        System.out.printf("SelfIndex=%s%n", selfIndex);
        System.out.printf("MapHash=%d SelfMapHash=%d Size=%dx%d%n", mapHash, selfMapHash, map.width(), map.height());
        System.out.printf("Profile: size=%d mineralDensity=%d baseAltitudeNoiseSize=%d baseMoistureNoiseSize=%d%n",
            profile.size(), profile.mineralDensity(), profile.baseAltitudeNoiseSize(), profile.baseMoistureNoiseSize());

        System.out.printf("%nTerrain sample (%dx%d, letters: S=Sea P=Plain F=Forest M=Mountain)%n", sampleSize, sampleSize);
        printTerrainLetterGrid(map, sampleSize);
        System.out.printf("%nANSI terrain+ore sample (%dx%d, ore overlays mountains)%n", sampleSize, sampleSize);
        System.out.println("Plain=green, Forest=dark green, Mountain=light brown, Sea=aqua");
        System.out.println("Ore overlay on mountains: Coal=black Iron=silver Gold=gold Bauxite=taupe");
        printTerrainAnsiGrid(map, sampleSize);
        System.out.println();
    }

    private static void printTerrainAnsiGrid(PlanetGeneration.PlanetMap map, int sampleSize) {
        if (map.width() < sampleSize || map.height() < sampleSize) {
            throw new IllegalArgumentException("Planet size is smaller than requested sample size");
        }
        int xOffset = (map.width() - sampleSize) / 2;
        int yOffset = (map.height() - sampleSize) / 2;
        for (int y = 0; y < sampleSize; y++) {
            StringBuilder row = new StringBuilder(sampleSize * 20);
            for (int x = 0; x < sampleSize; x++) {
                int mx = x + xOffset;
                int my = y + yOffset;
                var terrain = map.terrainTypes()[mx][my];
                var ore = map.oreTypes()[mx][my];
                row.append(renderAnsiCell(terrain, ore));
            }
            row.append(ANSI_RESET);
            System.out.println(row);
        }
    }

    private static String renderAnsiCell(PlanetGeneration.TerrainType terrain, PlanetGeneration.OreType ore) {
        if (ore != null) {
            return switch (ore) {
                case Ore_Coal -> ANSI_BG_COAL + ANSI_FG_LIGHT + "C ";
                case Ore_Iron -> ANSI_BG_IRON + ANSI_FG_DARK + "I ";
                case Ore_Gold -> ANSI_BG_GOLD + ANSI_FG_DARK + "G ";
                case Ore_Bauxite -> ANSI_BG_BAUXITE + ANSI_FG_LIGHT + "B ";
            };
        }
        return switch (terrain) {
            case TerrainType_Sea -> ANSI_BG_AQUA + ANSI_FG_DARK + "~ ";
            case TerrainType_Plain -> ANSI_BG_GRASS + ANSI_FG_DARK + ". ";
            case TerrainType_Forest -> ANSI_BG_FOREST + ANSI_FG_LIGHT + "T ";
            case TerrainType_Mountain -> ANSI_BG_MOUNTAIN + ANSI_FG_DARK + "^ ";
        };
    }

    private static void printKnownHierarchyCheck() {
        String universeMapKey = "Weathering.MapOfUniverse";
        String galaxyMapKey = "Weathering.MapOfGalaxy#=1,4";
        String planetSystemMapKey = "Weathering.MapOfStarSystem#=1,4=14,93";
        String planetMapKey = STARTING_PLANET_MAP_KEY;

        long universeHash = Hashing.hashString(universeMapKey);
        long galaxyHash = Hashing.hashString(galaxyMapKey);
        long starSystemHash = Hashing.hashString(planetSystemMapKey);
        long universeTileHash = Hashing.hash(1, 4, 100, 100, (int) universeHash);
        long galaxyTileHash = Hashing.hash(14, 93, 100, 100, (int) galaxyHash);

        var stars = CelestialGeneration.computeStarPositions(starSystemHash);
        long planetTileHash = Hashing.hash(24, 31, 32, 32, (int) starSystemHash);
        var body = CelestialGeneration.classifyBody(planetTileHash, starSystemHash, 24, 31, stars);
        boolean isPlanetLike = body.name().startsWith("Planet") || body == CelestialGeneration.BodyType.GasGiant || body == CelestialGeneration.BodyType.GasGiantRinged;

        System.out.println("=== Hierarchy Spot Check ===");
        System.out.printf("Universe tile (1,4) in %s -> galaxy=%s (tileHash=%d)%n", universeMapKey,
            CelestialGeneration.isGalaxyTile(universeTileHash), universeTileHash);
        System.out.printf("Galaxy tile (14,93) in %s -> planetSystem=%s (tileHash=%d)%n", galaxyMapKey,
            CelestialGeneration.isStarSystemTile(galaxyTileHash), galaxyTileHash);
        System.out.printf("Body tile (24,31) in %s -> %s (planetLike=%s)%n", planetSystemMapKey, body, isPlanetLike);

        long planetMapHash = Hashing.hashString(planetMapKey);
        long planetSelfMapHash = Hashing.hashString(selfMapKeyIndex(planetMapKey));
        var map = PlanetGeneration.generate(planetMapHash, planetSelfMapHash, 5);
        boolean inBounds = 24 < map.width() && 31 < map.height();
        System.out.printf("Planet tile (24,31) in %s -> inBounds=%s terrain=%s ore=%s%n%n",
            planetMapKey, inBounds, inBounds ? map.terrainTypes()[24][31] : "n/a", inBounds ? map.oreTypes()[24][31] : "n/a");
    }

    private static void printTerrainLetterGrid(PlanetGeneration.PlanetMap map, int sampleSize) {
        if (map.width() < sampleSize || map.height() < sampleSize) {
            throw new IllegalArgumentException("Planet size is smaller than requested sample size");
        }
        int xOffset = (map.width() - sampleSize) / 2;
        int yOffset = (map.height() - sampleSize) / 2;
        for (int y = 0; y < sampleSize; y++) {
            StringBuilder row = new StringBuilder(sampleSize);
            for (int x = 0; x < sampleSize; x++) {
                var terrain = map.terrainTypes()[x + xOffset][y + yOffset];
                row.append(terrainToLetter(terrain));
            }
            System.out.println(row);
        }
    }

    private static char terrainToLetter(PlanetGeneration.TerrainType terrain) {
        return switch (terrain) {
            case TerrainType_Sea -> 'S';
            case TerrainType_Plain -> 'P';
            case TerrainType_Forest -> 'F';
            case TerrainType_Mountain -> 'M';
        };
    }

    private static String selfMapKeyIndex(String mapKey) {
        int index = mapKey.indexOf('#');
        if (index < 0) {
            throw new IllegalArgumentException("Invalid map key (missing #): " + mapKey);
        }
        return mapKey.substring(index);
    }

    private static void printUniverseReport(long mapHash) {
        final int width = 100;
        final int height = 100;
        int galaxyCount = 0;

        System.out.println("=== Universe Report ===");
        System.out.printf("MapHash=%d size=%dx%d%n", mapHash, width, height);
        System.out.println("Sample tiles (x,y -> tileHash -> isGalaxy):");

        int[][] samples = new int[][] { {0, 0}, {1, 4}, {14, 93}, {24, 31}, {99, 99} };
        for (int[] sample : samples) {
            long tileHash = Hashing.hash(sample[0], sample[1], width, height, (int) mapHash);
            boolean isGalaxy = CelestialGeneration.isGalaxyTile(tileHash);
            System.out.printf("  (%d,%d) -> %d -> %s%n", sample[0], sample[1], tileHash, isGalaxy);
        }

        for (int i = 0; i < width; i++) {
            for (int j = 0; j < height; j++) {
                long tileHash = Hashing.hash(i, j, width, height, (int) mapHash);
                if (CelestialGeneration.isGalaxyTile(tileHash)) galaxyCount++;
            }
        }
        System.out.printf("Galaxy tiles in map=%d / %d%n%n", galaxyCount, width * height);
    }

    private static void printGalaxyReport(long mapHash) {
        final int width = 100;
        final int height = 100;
        int starSystemCount = 0;

        System.out.println("=== Galaxy Report ===");
        System.out.printf("MapHash=%d size=%dx%d%n", mapHash, width, height);
        System.out.println("Sample tiles (x,y -> tileHash -> isStarSystem):");

        int[][] samples = new int[][] { {0, 0}, {2, 17}, {14, 93}, {24, 31}, {99, 99} };
        for (int[] sample : samples) {
            long tileHash = Hashing.hash(sample[0], sample[1], width, height, (int) mapHash);
            boolean isStarSystem = CelestialGeneration.isStarSystemTile(tileHash);
            System.out.printf("  (%d,%d) -> %d -> %s%n", sample[0], sample[1], tileHash, isStarSystem);
        }

        for (int i = 0; i < width; i++) {
            for (int j = 0; j < height; j++) {
                long tileHash = Hashing.hash(i, j, width, height, (int) mapHash);
                if (CelestialGeneration.isStarSystemTile(tileHash)) starSystemCount++;
            }
        }
        System.out.printf("Star-system tiles in map=%d / %d%n%n", starSystemCount, width * height);
    }

    private static void printStarSystemReport(long mapHash) {
        final int width = 32;
        final int height = 32;

        var stars = CelestialGeneration.computeStarPositions(mapHash);
        var starType = CelestialGeneration.calculateStarType(mapHash);

        System.out.println("=== Star System Report ===");
        System.out.printf("MapHash=%d size=%dx%d%n", mapHash, width, height);
        System.out.printf("PrimaryStar=(%d,%d) type=%s%n", stars.x(), stars.y(), starType);
        System.out.printf("HasSecondStar=%s SecondStar=(%d,%d)%n", stars.hasSecondStar(), stars.secondStarX(), stars.secondStarY());

        Map<CelestialGeneration.BodyType, Integer> histogram = new EnumMap<>(CelestialGeneration.BodyType.class);
        for (int i = 0; i < width; i++) {
            for (int j = 0; j < height; j++) {
                long tileHash = Hashing.hash(i, j, width, height, (int) mapHash);
                var body = CelestialGeneration.classifyBody(tileHash, mapHash, i, j, stars);
                histogram.put(body, histogram.getOrDefault(body, 0) + 1);
            }
        }

        System.out.println("Body histogram:");
        for (var e : histogram.entrySet()) {
            System.out.printf("  %-24s %d%n", e.getKey(), e.getValue());
        }

        int[][] samples = new int[][] {
            {stars.x(), stars.y()},
            {0, 0}, {3, 7}, {10, 14}, {31, 31}
        };
        System.out.println("Sample body classification (x,y -> body):");
        for (int[] sample : samples) {
            long tileHash = Hashing.hash(sample[0], sample[1], width, height, (int) mapHash);
            var body = CelestialGeneration.classifyBody(tileHash, mapHash, sample[0], sample[1], stars);
            System.out.printf("  (%d,%d) -> %s%n", sample[0], sample[1], body);
        }
        System.out.println();
    }

    private static void printPlanetReport(long mapHash, long selfMapHash) {
        var profile = PlanetGeneration.profile(mapHash, selfMapHash);
        var map = PlanetGeneration.generate(mapHash, selfMapHash, 5);

        int sea = 0, plain = 0, forest = 0, mountain = 0;
        int minAltitude = Integer.MAX_VALUE;
        int maxAltitude = Integer.MIN_VALUE;
        int minMoisture = Integer.MAX_VALUE;
        int maxMoisture = Integer.MIN_VALUE;
        int minTemperature = Integer.MAX_VALUE;
        int maxTemperature = Integer.MIN_VALUE;

        for (int i = 0; i < map.width(); i++) {
            for (int j = 0; j < map.height(); j++) {
                minAltitude = Math.min(minAltitude, map.altitudes()[i][j]);
                maxAltitude = Math.max(maxAltitude, map.altitudes()[i][j]);
                minMoisture = Math.min(minMoisture, map.moistures()[i][j]);
                maxMoisture = Math.max(maxMoisture, map.moistures()[i][j]);
                minTemperature = Math.min(minTemperature, map.temperatures()[i][j]);
                maxTemperature = Math.max(maxTemperature, map.temperatures()[i][j]);

                switch (map.terrainTypes()[i][j]) {
                    case TerrainType_Sea -> sea++;
                    case TerrainType_Plain -> plain++;
                    case TerrainType_Forest -> forest++;
                    case TerrainType_Mountain -> mountain++;
                }
            }
        }

        System.out.println("=== Planet Report ===");
        System.out.printf("MapHash=%d SelfMapHash=%d%n", mapHash, selfMapHash);
        System.out.printf("Profile: size=%d mineralDensity=%d baseAltitudeNoiseSize=%d baseMoistureNoiseSize=%d%n",
            profile.size(), profile.mineralDensity(), profile.baseAltitudeNoiseSize(), profile.baseMoistureNoiseSize());

        System.out.printf("AltitudeRange=[%d,%d] MoistureRange=[%d,%d] TemperatureRange=[%d,%d]%n",
            minAltitude, maxAltitude, minMoisture, maxMoisture, minTemperature, maxTemperature);
        System.out.printf("TerrainHistogram: Sea=%d Plain=%d Forest=%d Mountain=%d Total=%d%n",
            sea, plain, forest, mountain, map.width() * map.height());

        System.out.println("Sample cells (x,y): altitude/moisture/temperature/terrain");
        int[][] samples = new int[][] {
            {0, 0},
            {map.width() / 4, map.height() / 4},
            {map.width() / 2, map.height() / 2},
            {map.width() - 1, map.height() - 1}
        };
        for (int[] sample : samples) {
            int x = sample[0];
            int y = sample[1];
            System.out.printf("  (%d,%d): %d / %d / %d / %s%n", x, y,
                map.altitudes()[x][y], map.moistures()[x][y], map.temperatures()[x][y], map.terrainTypes()[x][y]);
        }
        System.out.println();
    }
}
