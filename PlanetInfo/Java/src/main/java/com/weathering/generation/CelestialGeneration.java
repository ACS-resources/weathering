package com.weathering.generation;

public final class CelestialGeneration {
    private CelestialGeneration() {}

    public enum StarType { StarBlue, StarWhite, StarYellow, StarOrange, StarRed }
    public enum BodyType {
        PlanetBarren, PlanetArid, PlanetOcean, PlanetMolten, PlanetFrozen, PlanetContinental,
        PlanetGaia, PlanetSuperDimensional, GasGiant, GasGiantRinged, Asteroid, SpaceEmptiness,
        StarBlue, StarWhite, StarYellow, StarOrange, StarRed
    }

    public static boolean isGalaxyTile(long tileHashCode) {
        return tileHashCode % 50 == 0;
    }

    public static boolean isStarSystemTile(long tileHashCode) {
        return tileHashCode % 200 == 0;
    }

    public static StarType calculateStarType(long hashcode) {
        return switch ((int) (hashcode % 5)) {
            case 0 -> StarType.StarBlue;
            case 1 -> StarType.StarWhite;
            case 2 -> StarType.StarYellow;
            case 3 -> StarType.StarOrange;
            case 4 -> StarType.StarRed;
            default -> throw new IllegalStateException();
        };
    }

    public record StarPositions(int x, int y, boolean hasSecondStar, int secondStarX, int secondStarY) {}

    public static StarPositions computeStarPositions(long mapHashCode) {
        final int width = 32;
        final int height = 32;
        int starPos = abs((int) (mapHashCode % (height * height)));
        int x = starPos % width;
        int y = starPos / height;

        boolean hasSecondStar = mapHashCode % 1 == 0;
        int secondX = 0;
        int secondY = 0;
        if (hasSecondStar) {
            int secondStarPos = abs((int) Hashing.hash32(mapHashCode));
            if (secondStarPos == starPos) {
                hasSecondStar = false;
            } else {
                secondX = secondStarPos % width;
                secondY = secondStarPos / height;
            }
        }
        return new StarPositions(x, y, hasSecondStar, secondX, secondY);
    }

    public static BodyType classifyBody(long tileHashCode, long selfMapHashCode, int x, int y, StarPositions stars) {
        boolean isStar = (stars.x == x && stars.y == y) || (stars.hasSecondStar && stars.secondStarX == x && stars.secondStarY == y);
        if (isStar) {
            return switch (calculateStarType(selfMapHashCode)) {
                case StarBlue -> BodyType.StarBlue;
                case StarWhite -> BodyType.StarWhite;
                case StarYellow -> BodyType.StarYellow;
                case StarOrange -> BodyType.StarOrange;
                case StarRed -> BodyType.StarRed;
            };
        }

        Hashing.UIntRef h = new Hashing.UIntRef(Hashing.hash32(tileHashCode));
        if (Hashing.hashed(h) % 50 != 0) return BodyType.SpaceEmptiness;
        if (Hashing.hashed(h) % 2 != 0) return BodyType.Asteroid;
        if (Hashing.hashed(h) % 40 == 0) return BodyType.PlanetGaia;
        if (Hashing.hashed(h) % 40 == 0) return BodyType.PlanetSuperDimensional;
        if (Hashing.hashed(h) % 10 == 0) return BodyType.GasGiant;
        if (Hashing.hashed(h) % 9 == 0) return BodyType.GasGiantRinged;
        if (Hashing.hashed(h) % 3 == 0) return BodyType.PlanetContinental;
        if (Hashing.hashed(h) % 2 == 0) return BodyType.PlanetMolten;
        if (Hashing.hashed(h) % 4 == 0) return BodyType.PlanetBarren;
        if (Hashing.hashed(h) % 3 == 0) return BodyType.PlanetArid;
        if (Hashing.hashed(h) % 2 == 0) return BodyType.PlanetFrozen;
        return BodyType.PlanetOcean;
    }

    private static int abs(int x) { return x >= 0 ? x : -x; }
}
