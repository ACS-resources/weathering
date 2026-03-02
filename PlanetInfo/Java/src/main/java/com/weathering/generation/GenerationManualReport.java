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
    private static final String UNIVERSE_MAP_KEY = "Weathering.MapOfUniverse#";
    private static final String GALAXY_MAP_KEY = "Weathering.MapOfGalaxy#=1,4";
    private static final String STAR_SYSTEM_MAP_KEY = "Weathering.MapOfStarSystem#=1,4=14,93";
    private static final String STAR_SYSTEM_SELF_INDEX = "#=1,4=14,93";
    private static final int LANDING_X = 4;
    private static final int LANDING_Y = 83;

    private GenerationManualReport() {}

    public static void main(String[] args) {
        long universeMapHash = Hashing.hashString(UNIVERSE_MAP_KEY);
        long galaxyMapHash = Hashing.hashString(GALAXY_MAP_KEY);
        long starSystemMapHash = Hashing.hashString(STAR_SYSTEM_MAP_KEY);
        long planetMapHash = Hashing.hashString(STARTING_PLANET_MAP_KEY);
        long planetSelfMapHash = Hashing.hashString(selfMapKeyIndex(STARTING_PLANET_MAP_KEY));

        printKnownHierarchyCheck();
        printUniverseReport(universeMapHash);
        printGalaxyReport(galaxyMapHash);
        long starSystemTypeHash = Hashing.hashString(STAR_SYSTEM_SELF_INDEX);

        printStarSystemReport(starSystemMapHash, starSystemTypeHash);
        printPlanetReport(planetMapHash, planetSelfMapHash);
        printStartingStarPlanetReport(STARTING_PLANET_MAP_KEY);
    }

    private static void printStartingStarPlanetReport(String mapKey) {
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

        System.out.printf("%nTerrain upside-down view around landing (%d,%d) (%dx%d)%n", LANDING_X, LANDING_Y, map.width(), map.height());
        printTerrainLetterGridUpsideDownAround(map, LANDING_X, LANDING_Y);
        System.out.printf("%nANSI terrain+ore upside-down view around landing (%d,%d) (%dx%d)%n", LANDING_X, LANDING_Y, map.width(), map.height());
        System.out.println("Plain=green, Forest=dark green, Mountain=light brown, Sea=aqua");
        System.out.println("Ore overlay on mountains: Coal=black Iron=silver Gold=gold Bauxite=taupe");
        printTerrainAnsiGridUpsideDownAround(map, LANDING_X, LANDING_Y);
        System.out.println();
    }

    private static void printTerrainAnsiGrid(PlanetGeneration.PlanetMap map) {
        for (int y = 0; y < map.height(); y++) {
            StringBuilder row = new StringBuilder(map.width() * 20);
            for (int x = 0; x < map.width(); x++) {
                var terrain = map.terrainTypes()[x][y];
                var ore = map.oreTypes()[x][y];
                row.append(renderAnsiCell(terrain, ore));
            }
            row.append(ANSI_RESET);
            System.out.println(row);
        }
    }

    private static void printTerrainAnsiGridUpsideDownAround(PlanetGeneration.PlanetMap map, int centerX, int centerY) {
        int xOrigin = centerX - map.width() / 2;
        int yOrigin = centerY - map.height() / 2;
        printTopAxis(xOrigin, map.width());
        for (int y = 0; y < map.height(); y++) {
            int worldY = floorMod(yOrigin + (map.height() - 1 - y), map.height());
            StringBuilder row = new StringBuilder(map.width() * 20 + 8);
            row.append(String.format("%3d ", worldY));
            for (int x = 0; x < map.width(); x++) {
                int worldX = floorMod(xOrigin + x, map.width());
                var terrain = map.terrainTypes()[worldX][worldY];
                var ore = map.oreTypes()[worldX][worldY];
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
        String universeMapKey = UNIVERSE_MAP_KEY;
        String galaxyMapKey = GALAXY_MAP_KEY;
        String planetSystemMapKey = STAR_SYSTEM_MAP_KEY;
        String planetMapKey = STARTING_PLANET_MAP_KEY;

        long universeHash = Hashing.hashString(universeMapKey);
        long galaxyHash = Hashing.hashString(galaxyMapKey);
        long starSystemHash = Hashing.hashString(planetSystemMapKey);
        long universeTileHash = Hashing.hash(1, 4, 100, 100, (int) universeHash);
        long galaxyTileHash = Hashing.hash(14, 93, 100, 100, (int) galaxyHash);

        long starSystemTypeHash = Hashing.hashString(STAR_SYSTEM_SELF_INDEX);
        var stars = CelestialGeneration.computeStarPositions(starSystemHash);
        long planetTileHash = Hashing.hash(24, 31, 32, 32, (int) starSystemHash);
        var body = CelestialGeneration.classifyBody(planetTileHash, starSystemTypeHash, 24, 31, stars);
        boolean isPlanetLike = body.name().startsWith("Planet") || body == CelestialGeneration.BodyType.GasGiant || body == CelestialGeneration.BodyType.GasGiantRinged;

        int starTiles = 0;
        int planetLikeBodies = 0;
        for (int y = 0; y < 32; y++) {
            for (int x = 0; x < 32; x++) {
                long tileHash = Hashing.hash(x, y, 32, 32, (int) starSystemHash);
                var classification = CelestialGeneration.classifyBody(tileHash, starSystemTypeHash, x, y, stars);
                if (classification.name().startsWith("Star")) starTiles++;
                if (classification.name().startsWith("Planet")
                    || classification == CelestialGeneration.BodyType.GasGiant
                    || classification == CelestialGeneration.BodyType.GasGiantRinged) {
                    planetLikeBodies++;
                }
            }
        }

        System.out.println("=== Hierarchy Spot Check ===");
        System.out.printf("Universe tile (1,4) in %s -> galaxy=%s (tileHash=%d)%n", universeMapKey,
            CelestialGeneration.isGalaxyTile(universeTileHash), universeTileHash);
        System.out.printf("Galaxy tile (14,93) in %s -> planetSystem=%s (tileHash=%d)%n", galaxyMapKey,
            CelestialGeneration.isStarSystemTile(galaxyTileHash), galaxyTileHash);
        System.out.printf("Body tile (24,31) in %s -> %s (planetLike=%s)%n", planetSystemMapKey, body, isPlanetLike);
        System.out.printf("Star-system totals in %s -> stars=%d planetLikeBodies=%d starType=%s%n", planetSystemMapKey, starTiles, planetLikeBodies, CelestialGeneration.calculateStarType(starSystemTypeHash));

        long planetMapHash = Hashing.hashString(planetMapKey);
        long planetSelfMapHash = Hashing.hashString(selfMapKeyIndex(planetMapKey));
        var map = PlanetGeneration.generate(planetMapHash, planetSelfMapHash, 5);
        boolean inBounds = 24 < map.width() && 31 < map.height();
        System.out.printf("Planet tile (24,31) in %s -> inBounds=%s terrain=%s ore=%s%n%n",
            planetMapKey, inBounds, inBounds ? map.terrainTypes()[24][31] : "n/a", inBounds ? map.oreTypes()[24][31] : "n/a");
    }

    private static void printTerrainLetterGrid(PlanetGeneration.PlanetMap map) {
        for (int y = 0; y < map.height(); y++) {
            StringBuilder row = new StringBuilder(map.width());
            for (int x = 0; x < map.width(); x++) {
                var terrain = map.terrainTypes()[x][y];
                row.append(terrainToLetter(terrain)).append(" ");
            }
            System.out.println(row);
        }
    }

    private static void printTerrainLetterGridUpsideDownAround(PlanetGeneration.PlanetMap map, int centerX, int centerY) {
        int xOrigin = centerX - map.width() / 2;
        int yOrigin = centerY - map.height() / 2;
        printTopAxis(xOrigin, map.width());
        for (int y = 0; y < map.height(); y++) {
            int worldY = floorMod(yOrigin + (map.height() - 1 - y), map.height());
            StringBuilder row = new StringBuilder(map.width() * 2 + 8);
            row.append(String.format("%3d ", worldY));
            for (int x = 0; x < map.width(); x++) {
                int worldX = floorMod(xOrigin + x, map.width());
                var terrain = map.terrainTypes()[worldX][worldY];
                row.append(terrainToLetter(terrain)).append(" ");
            }
            System.out.println(row);
        }
    }


    private static void printTopAxis(int xOrigin, int width) {
        StringBuilder header = new StringBuilder(width * 2 + 8);
        header.append("    ");
        for (int x = 0; x < width; x++) {
            int worldX = floorMod(xOrigin + x, width);
            header.append(compressedCoord(worldX));
        }
        System.out.println(header);
    }

    private static String compressedCoord(int index) {
        int high = index / 10;
        int low = index % 10;
        return String.format("%X%d", high, low);
    }

    private static int floorMod(int value, int modulus) {
        int result = value % modulus;
        return result < 0 ? result + modulus : result;
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
        System.out.println("Sample galaxy tiles (x,y -> tileHash):");
        printUniverseGalaxySamples(mapHash, width, height, 5);

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
        System.out.println("Sample star-system tiles (x,y -> tileHash):");
        printGalaxySystemSamples(mapHash, width, height, 5);

        for (int i = 0; i < width; i++) {
            for (int j = 0; j < height; j++) {
                long tileHash = Hashing.hash(i, j, width, height, (int) mapHash);
                if (CelestialGeneration.isStarSystemTile(tileHash)) starSystemCount++;
            }
        }
        System.out.printf("Star-system tiles in map=%d / %d%n%n", starSystemCount, width * height);
    }

    private static void printStarSystemReport(long mapHash, long starTypeHash) {
        final int width = 32;
        final int height = 32;

        var stars = CelestialGeneration.computeStarPositions(mapHash);
        var starType = CelestialGeneration.calculateStarType(starTypeHash);

        System.out.println("=== Star System Report ===");
        System.out.printf("MapHash=%d size=%dx%d%n", mapHash, width, height);
        System.out.printf("PrimaryStar=(%d,%d) type=%s%n", stars.x(), stars.y(), starType);
        System.out.printf("HasSecondStar=%s SecondStar=(%d,%d)%n", stars.hasSecondStar(), stars.secondStarX(), stars.secondStarY());

        Map<CelestialGeneration.BodyType, Integer> histogram = new EnumMap<>(CelestialGeneration.BodyType.class);
        for (int i = 0; i < width; i++) {
            for (int j = 0; j < height; j++) {
                long tileHash = Hashing.hash(i, j, width, height, (int) mapHash);
                var body = CelestialGeneration.classifyBody(tileHash, starTypeHash, i, j, stars);
                histogram.put(body, histogram.getOrDefault(body, 0) + 1);
            }
        }

        System.out.println("Body histogram:");
        for (var e : histogram.entrySet()) {
            System.out.printf("  %-24s %d%n", e.getKey(), e.getValue());
        }

        System.out.println("Sample non-empty body classification (x,y -> body):");
        printStarSystemNonEmptySamples(mapHash, starTypeHash, stars, width, height, 6);
        System.out.println();
    }


    private static void printUniverseGalaxySamples(long mapHash, int width, int height, int limit) {
        int printed = 0;
        for (int y = 0; y < height && printed < limit; y++) {
            for (int x = 0; x < width && printed < limit; x++) {
                long tileHash = Hashing.hash(x, y, width, height, (int) mapHash);
                if (CelestialGeneration.isGalaxyTile(tileHash)) {
                    System.out.printf("  (%d,%d) -> %d%n", x, y, tileHash);
                    printed++;
                }
            }
        }
    }

    private static void printGalaxySystemSamples(long mapHash, int width, int height, int limit) {
        int printed = 0;
        for (int y = 0; y < height && printed < limit; y++) {
            for (int x = 0; x < width && printed < limit; x++) {
                long tileHash = Hashing.hash(x, y, width, height, (int) mapHash);
                if (CelestialGeneration.isStarSystemTile(tileHash)) {
                    System.out.printf("  (%d,%d) -> %d%n", x, y, tileHash);
                    printed++;
                }
            }
        }
    }

    private static void printStarSystemNonEmptySamples(long mapHash, long starTypeHash, CelestialGeneration.StarPositions stars, int width, int height, int limit) {
        int printed = 0;
        for (int y = 0; y < height && printed < limit; y++) {
            for (int x = 0; x < width && printed < limit; x++) {
                long tileHash = Hashing.hash(x, y, width, height, (int) mapHash);
                var body = CelestialGeneration.classifyBody(tileHash, starTypeHash, x, y, stars);
                if (body != CelestialGeneration.BodyType.SpaceEmptiness) {
                    System.out.printf("  (%d,%d) -> %s%n", x, y, body);
                    printed++;
                }
            }
        }
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
