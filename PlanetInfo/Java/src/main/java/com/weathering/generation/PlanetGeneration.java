package com.weathering.generation;

public final class PlanetGeneration {
    private PlanetGeneration() {}

    public enum AltitudeType { AltitudeSea, AltitudePlain, AltitudeMountain }
    public enum MoistureType { MoistureDesert, MoistureGrassland, MoistureForest }
    public enum TemperatureType { TemporatureTemporate, TemporatureCold }
    public enum TerrainType { TerrainType_Sea, TerrainType_Plain, TerrainType_Forest, TerrainType_Mountain }
    public enum OreType { Ore_Coal, Ore_Iron, Ore_Gold, Ore_Bauxite }

    public record PlanetProfile(int size, int mineralDensity, int baseAltitudeNoiseSize, int baseMoistureNoiseSize) {}

    public record PlanetMap(int width, int height, int[][] altitudes, AltitudeType[][] altitudeTypes,
                            int[][] moistures, MoistureType[][] moistureTypes,
                            int[][] temperatures, TemperatureType[][] temperatureTypes,
                            TerrainType[][] terrainTypes,
                            OreType[][] oreTypes) {}

    public static int calculatePlanetSize(long selfMapHashCode) {
        return 50 + (int) (selfMapHashCode % 100);
    }

    public static int calculateMineralDensity(long selfMapHashCode) {
        return 3 + (int) (Hashing.addSalt(selfMapHashCode, 2641779086L) % 27);
    }

    public static PlanetProfile profile(long mapHashCode, long selfMapHashCode) {
        int size = calculatePlanetSize(selfMapHashCode);
        int baseAltitudeNoiseSize = 5 + (int) (mapHashCode % 11);
        int baseMoistureNoiseSize = 7 + (int) (mapHashCode % 17);
        return new PlanetProfile(size, calculateMineralDensity(selfMapHashCode), baseAltitudeNoiseSize, baseMoistureNoiseSize);
    }

    public static PlanetMap generate(long mapHashCode, long selfMapHashCode, int randomSeed) {
        PlanetProfile p = profile(mapHashCode, selfMapHashCode);
        int width = p.size;
        int height = p.size;

        int[][] altitudes = new int[width][height];
        AltitudeType[][] altitudeTypes = new AltitudeType[width][height];
        int[][] moistures = new int[width][height];
        MoistureType[][] moistureTypes = new MoistureType[width][height];
        int[][] temperatures = new int[width][height];
        TemperatureType[][] temperatureTypes = new TemperatureType[width][height];
        TerrainType[][] terrainTypes = new TerrainType[width][height];
        OreType[][] oreTypes = new OreType[width][height];

        int autoInc = randomSeed;
        int offset0 = autoInc++;
        int offset1 = autoInc++;
        int offset2 = autoInc++;

        int noise0 = p.baseAltitudeNoiseSize;
        int noise1 = noise0 * 2;
        int noise2 = noise1 * 2;
        for (int i = 0; i < width; i++) {
            for (int j = 0; j < height; j++) {
                float n0 = Hashing.perlinNoise((float) noise0 * i / width, (float) noise0 * j / height, noise0, noise0, offset0 + (int) mapHashCode);
                float n1 = Hashing.perlinNoise((float) noise1 * i / width, (float) noise1 * j / height, noise1, noise1, offset1 + (int) mapHashCode);
                float n2 = Hashing.perlinNoise((float) noise2 * i / width, (float) noise2 * j / height, noise2, noise2, offset2 + (int) mapHashCode);
                float f = (n0 * 4 + n1 * 2 + n2 + 7) / 14f;
                int altitude = lerpInt(-10000, 9500, f);
                altitudes[i][j] = altitude;
                altitudeTypes[i][j] = getAltitudeType(altitude);
            }
        }

        int mOffset = autoInc++;
        int mSize = p.baseMoistureNoiseSize;
        for (int i = 0; i < width; i++) {
            for (int j = 0; j < height; j++) {
                float n = Hashing.perlinNoise((float) mSize * i / width, (float) mSize * j / height, mSize, mSize, mOffset + (int) mapHashCode);
                float f = (n + 1) / 2f;
                int moisture = lerpInt(0, 100, f);
                moistures[i][j] = moisture;
                moistureTypes[i][j] = getMoistureType(moisture);
            }
        }

        int tOffset = autoInc++;
        int tSize = 4;
        for (int i = 0; i < width; i++) {
            for (int j = 0; j < height; j++) {
                float n = Hashing.perlinNoise((float) tSize * i / width, (float) tSize * j / height, tSize, tSize, tOffset + (int) mapHashCode);
                n = (n + 1) / 2f;
                float latitude = (float) Math.sin(Math.PI * j / width);
                float f = lerp(n, latitude, 0f);
                int temperature = -20 + (int) (f * (40 - (-20)));
                temperatures[i][j] = temperature;
                temperatureTypes[i][j] = getTemperatureType(temperature);
                terrainTypes[i][j] = deriveTerrain(altitudeTypes[i][j], moistureTypes[i][j], temperatureTypes[i][j]);
                oreTypes[i][j] = generateOreType(mapHashCode, selfMapHashCode, p.mineralDensity(), i, j, terrainTypes[i][j]);
            }
        }

        return new PlanetMap(width, height, altitudes, altitudeTypes, moistures, moistureTypes, temperatures, temperatureTypes, terrainTypes, oreTypes);
    }

    static OreType generateOreType(long mapHashCode, long selfMapHashCode, int mineralDensity, int x, int y, TerrainType terrain) {
        if (terrain != TerrainType.TerrainType_Mountain) {
            return null;
        }
        long oreNoise = Hashing.hash(x, y, 257, 509, (int) Hashing.addSalt(selfMapHashCode ^ mapHashCode, 0x4F52454CL));
        long oreRoll = Math.floorMod(oreNoise, 100);
        int spawnChance = Math.min(70, Math.max(15, mineralDensity * 2));
        if (oreRoll >= spawnChance) {
            return null;
        }
        int oreKind = (int) Math.floorMod(Hashing.hash32(oreNoise), 4);
        return switch (oreKind) {
            case 0 -> OreType.Ore_Coal;
            case 1 -> OreType.Ore_Iron;
            case 2 -> OreType.Ore_Gold;
            case 3 -> OreType.Ore_Bauxite;
            default -> throw new IllegalStateException();
        };
    }

    static AltitudeType getAltitudeType(int altitude) {
        if (altitude > 3000) return AltitudeType.AltitudeMountain;
        if (altitude > 0) return AltitudeType.AltitudePlain;
        return AltitudeType.AltitudeSea;
    }

    static MoistureType getMoistureType(int moisture) {
        if (moisture > 55) return MoistureType.MoistureForest;
        if (moisture > 35) return MoistureType.MoistureGrassland;
        return MoistureType.MoistureDesert;
    }

    static TemperatureType getTemperatureType(int temperature) {
        if (temperature > 0) return TemperatureType.TemporatureTemporate;
        return TemperatureType.TemporatureCold;
    }

    static TerrainType deriveTerrain(AltitudeType altitude, MoistureType moisture, TemperatureType temperature) {
        if (altitude != AltitudeType.AltitudeSea) {
            if (temperature == TemperatureType.TemporatureTemporate) {
                return moisture == MoistureType.MoistureForest ? TerrainType.TerrainType_Forest : TerrainType.TerrainType_Plain;
            }
            return TerrainType.TerrainType_Mountain;
        }
        return TerrainType.TerrainType_Sea;
    }

    private static int lerpInt(int min, int max, float t) {
        return (int) (min + (max - min) * t);
    }

    private static float lerp(float a, float b, float t) {
        return a + (b - a) * t;
    }
}
