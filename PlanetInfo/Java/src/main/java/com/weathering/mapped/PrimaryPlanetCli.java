package com.weathering.mapped;

import com.weathering.generation.PlanetGeneration;

import java.util.Locale;
import java.util.Scanner;

/**
 * Minimal non-Unity map renderer for the primary planet.
 * Controls: w/a/s/d to move camera, q to quit.
 */
public final class PrimaryPlanetCli {
    private static final int VIEW_WIDTH = 32;
    private static final int VIEW_HEIGHT = 18;

    private PrimaryPlanetCli() {}

    public static void main(String[] args) {
        PlanetGeneration.PlanetMap map = MappedPlanetGeneration.generatePrimaryPlanet();
        int cameraX = clamp(MappedPlanetGeneration.LANDING_X, 0, map.width() - 1);
        int cameraY = clamp(MappedPlanetGeneration.LANDING_Y, 0, map.height() - 1);

        try (Scanner scanner = new Scanner(System.in)) {
            while (true) {
                render(map, cameraX, cameraY);
                System.out.print("Command (w/a/s/d, q quit): ");
                if (!scanner.hasNextLine()) {
                    break;
                }
                String line = scanner.nextLine().trim().toLowerCase(Locale.ROOT);
                if (line.isEmpty()) {
                    continue;
                }
                char c = line.charAt(0);
                if (c == 'q') {
                    break;
                }
                switch (c) {
                    case 'w' -> cameraY = Math.max(0, cameraY - 1);
                    case 's' -> cameraY = Math.min(map.height() - 1, cameraY + 1);
                    case 'a' -> cameraX = Math.max(0, cameraX - 1);
                    case 'd' -> cameraX = Math.min(map.width() - 1, cameraX + 1);
                    default -> {
                    }
                }
            }
        }
    }

    private static void render(PlanetGeneration.PlanetMap map, int cameraX, int cameraY) {
        StringBuilder sb = new StringBuilder();
        sb.append("\n=== Primary Planet (raw render) ===\n");
        sb.append("Landing=").append(MappedPlanetGeneration.LANDING_X).append(',').append(MappedPlanetGeneration.LANDING_Y)
                .append(" Camera=").append(cameraX).append(',').append(cameraY)
                .append(" Size=").append(map.width()).append('x').append(map.height())
                .append("\n");

        int startX = clamp(cameraX - (VIEW_WIDTH / 2), 0, Math.max(0, map.width() - VIEW_WIDTH));
        int startY = clamp(cameraY - (VIEW_HEIGHT / 2), 0, Math.max(0, map.height() - VIEW_HEIGHT));
        int endX = Math.min(map.width(), startX + VIEW_WIDTH);
        int endY = Math.min(map.height(), startY + VIEW_HEIGHT);

        sb.append("   ");
        for (int x = startX; x < endX; x++) {
            sb.append(String.format("%02d", x % 100)).append(' ');
        }
        sb.append('\n');

        for (int y = startY; y < endY; y++) {
            sb.append(String.format("%02d ", y % 100));
            for (int x = startX; x < endX; x++) {
                sb.append(symbol(map, x, y)).append("  ");
            }
            sb.append('\n');
        }
        sb.append("Legend: S sea, P plain, F forest, M mountain, c copper, C coal, I iron, G gold, B bauxite\n");
        System.out.println(sb);
    }

    private static char symbol(PlanetGeneration.PlanetMap map, int x, int y) {
        PlanetGeneration.OreType ore = map.oreTypes()[x][y];
        if (ore != null) {
            return switch (ore) {
                case Ore_Copper -> 'c';
                case Ore_Coal -> 'C';
                case Ore_Iron -> 'I';
                case Ore_Gold -> 'G';
                case Ore_Bauxite -> 'B';
            };
        }
        return switch (map.terrainTypes()[x][y]) {
            case TerrainType_Sea -> 'S';
            case TerrainType_Plain -> 'P';
            case TerrainType_Forest -> 'F';
            case TerrainType_Mountain -> 'M';
        };
    }

    private static int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }
}
