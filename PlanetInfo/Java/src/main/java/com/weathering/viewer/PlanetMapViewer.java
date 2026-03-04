package com.weathering.viewer;

import com.weathering.generation.Hashing;
import com.weathering.generation.PlanetGeneration;

import javax.imageio.ImageIO;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.SwingUtilities;
import javax.swing.Timer;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class PlanetMapViewer {
    private PlanetMapViewer() {}

    private static final int TILE_SIZE = 16;
    private static final int WINDOW_WIDTH = 1280;
    private static final int WINDOW_HEIGHT = 720;
    private static final double CAMERA_SPEED_TILES_PER_SECOND = 8.0;

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            long primaryPlanetHash = Hashing.hashString("Weathering.MapOfPlanet#=1,4=14,93=24,31");
            var map = PlanetGeneration.generate(primaryPlanetHash, primaryPlanetHash, 5);

            JFrame frame = new JFrame("Weathering Primary Planet (Java)");
            frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            frame.setContentPane(new PlanetMapPanel(map));
            frame.pack();
            frame.setLocationRelativeTo(null);
            frame.setVisible(true);
        });
    }

    private static final class PlanetMapPanel extends JPanel {
        private final PlanetGeneration.PlanetMap map;
        private final BufferedImage grassSheet;
        private final BufferedImage hillSheet;
        private final BufferedImage waterSurface;
        private final BufferedImage waterWave;
        private final BufferedImage tree;

        private double cameraX;
        private double cameraY;
        private final Set<Integer> pressedKeys = new HashSet<>();
        private long lastTickNanos = System.nanoTime();

        PlanetMapPanel(PlanetGeneration.PlanetMap map) {
            this.map = map;
            this.grassSheet = loadImage("tiles/Planets/Continental/PlanetContinental_Grass.png");
            this.hillSheet = loadImage("tiles/Planets/Continental/PlanetContinental_Hill.png");
            this.waterSurface = loadImage("tiles/Planets/Continental/PlanetContinental_WaterSurface.png");
            this.waterWave = loadImage("tiles/Planets/Continental/PlanetContinental_WaterWave.png");
            this.tree = loadImage("tiles/Planets/Continental/PlanetContinental_Tree.png");

            this.cameraX = map.width() / 2.0;
            this.cameraY = map.height() / 2.0;

            setPreferredSize(new Dimension(WINDOW_WIDTH, WINDOW_HEIGHT));
            setBackground(Color.BLACK);
            setFocusable(true);

            addKeyListener(new KeyAdapter() {
                @Override
                public void keyPressed(KeyEvent e) {
                    pressedKeys.add(e.getKeyCode());
                }

                @Override
                public void keyReleased(KeyEvent e) {
                    pressedKeys.remove(e.getKeyCode());
                }
            });

            Timer timer = new Timer(16, e -> {
                updateCamera();
                repaint();
            });
            timer.start();
        }

        private void updateCamera() {
            long now = System.nanoTime();
            double dt = (now - lastTickNanos) / 1_000_000_000.0;
            lastTickNanos = now;

            double speed = CAMERA_SPEED_TILES_PER_SECOND * dt;
            if (pressedKeys.contains(KeyEvent.VK_W)) cameraY -= speed;
            if (pressedKeys.contains(KeyEvent.VK_S)) cameraY += speed;
            if (pressedKeys.contains(KeyEvent.VK_A)) cameraX -= speed;
            if (pressedKeys.contains(KeyEvent.VK_D)) cameraX += speed;

            cameraX = wrapDouble(cameraX, map.width());
            cameraY = wrapDouble(cameraY, map.height());
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_NEAREST_NEIGHBOR);

            int tilesX = getWidth() / TILE_SIZE + 3;
            int tilesY = getHeight() / TILE_SIZE + 3;
            int startX = (int) Math.floor(cameraX - tilesX / 2.0);
            int startY = (int) Math.floor(cameraY - tilesY / 2.0);

            for (int sy = 0; sy < tilesY; sy++) {
                for (int sx = 0; sx < tilesX; sx++) {
                    int x = wrap(startX + sx, map.width());
                    int y = wrap(startY + sy, map.height());

                    int drawX = sx * TILE_SIZE;
                    int drawY = sy * TILE_SIZE;

                    drawBase(g2, x, y, drawX, drawY);
                    drawOverlays(g2, x, y, drawX, drawY);
                }
            }
        }

        private void drawBase(Graphics2D g2, int x, int y, int drawX, int drawY) {
            var terrain = map.terrainTypes()[x][y];
            if (terrain == PlanetGeneration.TerrainType.TerrainType_Sea) {
                boolean seaUp = map.terrainTypes()[x][wrap(y + 1, map.height())] == PlanetGeneration.TerrainType.TerrainType_Sea;
                g2.drawImage(seaUp ? waterSurface : waterWave, drawX, drawY, null);
                return;
            }

            int grassIndex = calculate4x4RuleTileIndex(x, y, t -> t != PlanetGeneration.TerrainType.TerrainType_Sea);
            if (grassIndex == 5) {
                long tileHash = Hashing.hash(x, y, map.width(), map.height(), 0x5EED1234);
                grassIndex = 16 + (int) (tileHash % 16);
            }
            drawFromSheet(g2, grassSheet, grassIndex, 4, drawX, drawY);
        }

        private void drawOverlays(Graphics2D g2, int x, int y, int drawX, int drawY) {
            var terrain = map.terrainTypes()[x][y];
            if (terrain == PlanetGeneration.TerrainType.TerrainType_Forest) {
                g2.drawImage(tree, drawX, drawY, null);
            } else if (terrain == PlanetGeneration.TerrainType.TerrainType_Mountain) {
                int hillIndex = calculate6x8RuleTileIndex(x, y, t -> t == PlanetGeneration.TerrainType.TerrainType_Mountain);
                drawFromSheet(g2, hillSheet, hillIndex, 8, drawX, drawY);
            }
        }

        private int calculate4x4RuleTileIndex(int x, int y, TerrainPredicate predicate) {
            boolean left = predicate.matches(map.terrainTypes()[wrap(x - 1, map.width())][y]);
            boolean right = predicate.matches(map.terrainTypes()[wrap(x + 1, map.width())][y]);
            boolean up = predicate.matches(map.terrainTypes()[x][wrap(y + 1, map.height())]);
            boolean down = predicate.matches(map.terrainTypes()[x][wrap(y - 1, map.height())]);
            if (left) {
                if (right) {
                    if (up) return down ? 5 : 9;
                    return down ? 1 : 13;
                }
                if (up) return down ? 6 : 10;
                return down ? 2 : 14;
            }
            if (right) {
                if (up) return down ? 4 : 8;
                return down ? 0 : 12;
            }
            if (up) return down ? 7 : 11;
            return down ? 3 : 15;
        }

        private int calculate6x8RuleTileIndex(int x, int y, TerrainPredicate predicate) {
            boolean left = predicate.matches(map.terrainTypes()[wrap(x - 1, map.width())][y]);
            boolean right = predicate.matches(map.terrainTypes()[wrap(x + 1, map.width())][y]);
            boolean up = predicate.matches(map.terrainTypes()[x][wrap(y + 1, map.height())]);
            boolean down = predicate.matches(map.terrainTypes()[x][wrap(y - 1, map.height())]);
            boolean upLeft = predicate.matches(map.terrainTypes()[wrap(x - 1, map.width())][wrap(y + 1, map.height())]);
            boolean upRight = predicate.matches(map.terrainTypes()[wrap(x + 1, map.width())][wrap(y + 1, map.height())]);
            boolean downLeft = predicate.matches(map.terrainTypes()[wrap(x - 1, map.width())][wrap(y - 1, map.height())]);
            boolean downRight = predicate.matches(map.terrainTypes()[wrap(x + 1, map.width())][wrap(y - 1, map.height())]);

            return calculate6x8RuleTileIndex(left, right, up, down, upLeft, upRight, downLeft, downRight);
        }

        private static int calculate6x8RuleTileIndex(boolean left, boolean right,
                                                     boolean up, boolean down, boolean upLeft, boolean upRight,
                                                     boolean downLeft, boolean downRight) {
            if (left) {
                if (right) {
                    if (up) {
                        if (down) {
                            if (upLeft && upRight && downLeft && downRight) return 1 * 8 + 1;

                            if (!upLeft && upRight && downLeft && downRight) return 5 * 8 + 2;
                            if (upLeft && !upRight && downLeft && downRight) return 5 * 8;
                            if (upLeft && upRight && !downLeft && downRight) return 3 * 8 + 2;
                            if (upLeft && upRight && downLeft && !downRight) return 3 * 8;

                            if (upLeft && upRight && !downLeft && !downRight) return 3 * 8 + 1;
                            if (upLeft && !upRight && downLeft && !downRight) return 4 * 8;
                            if (upLeft && !upRight && !downLeft && downRight) return 7;
                            if (!upLeft && upRight && downLeft && !downRight) return 6;
                            if (!upLeft && upRight && !downLeft && downRight) return 4 * 8 + 2;
                            if (!upLeft && !upRight && downLeft && downRight) return 5 * 8 + 1;

                            if (upLeft && !upRight && !downLeft && !downRight) return 2 * 8 + 7;
                            if (!upLeft && upRight && !downLeft && !downRight) return 2 * 8 + 6;
                            if (!upLeft && !upRight && downLeft && !downRight) return 1 * 8 + 7;
                            if (!upLeft && !upRight && !downLeft && downRight) return 1 * 8 + 6;

                            if (!upLeft && !upRight && !downLeft && !downRight) return 1 * 8 + 4;

                            throw new IllegalStateException();
                        } else {
                            if (upLeft && upRight) return 2 * 8 + 1;
                            if (!upLeft && upRight) return 4 * 8 + 6;
                            if (upLeft && !upRight) return 4 * 8 + 7;
                            if (!upLeft && !upRight) return 2 * 8 + 4;

                            throw new IllegalStateException();
                        }
                    } else {
                        if (down) {
                            if (downLeft && downRight) return 1;
                            if (!downLeft && downRight) return 3 * 8 + 6;
                            if (downLeft && !downRight) return 3 * 8 + 7;
                            if (!downLeft && !downRight) return 4;

                        } else {
                            return 5 * 8 + 5;
                        }
                    }
                } else {
                    if (up) {
                        if (down) {
                            if (upLeft && downLeft) return 1 * 8 + 2;
                            if (!upLeft && downLeft) return 3 * 8 + 5;
                            if (upLeft && !downLeft) return 4 * 8 + 5;
                            if (!upLeft && !downLeft) return 1 * 8 + 5;

                            throw new IllegalStateException();
                        } else {
                            if (upLeft) return 2 * 8 + 2;
                            return 2 * 8 + 5;
                        }
                    } else {
                        if (down) {
                            if (downLeft) return 2;
                            return 5;
                        } else {
                            return 5 * 8 + 6;
                        }
                    }
                }
            } else {
                if (right) {
                    if (up) {
                        if (down) {
                            if (upRight && downRight) return 1 * 8;
                            if (!upRight && downRight) return 3 * 8 + 4;
                            if (upRight && !downRight) return 4 * 8 + 4;
                            if (!upRight && !downRight) return 1 * 8 + 3;

                            throw new IllegalStateException();
                        } else {
                            if (upRight) return 2 * 8;
                            return 2 * 8 + 3;
                        }
                    } else {
                        if (down) {
                            if (downRight) return 0;
                            return 3;
                        } else {
                            return 5 * 8 + 4;
                        }
                    }
                } else {
                    if (up) {
                        if (down) {
                            return 4 * 8 + 3;
                        } else {
                            return 5 * 8 + 3;
                        }
                    } else {
                        if (down) {
                            return 3 * 8 + 3;
                        } else {
                            return 5 * 8 + 7;
                        }
                    }
                }
            }
            return 4 * 8 + 1;
        }

        private static void drawFromSheet(Graphics2D g2, BufferedImage sheet, int index, int cols, int x, int y) {
            int sx = (index % cols) * TILE_SIZE;
            int sy = (index / cols) * TILE_SIZE;
            if (sx + TILE_SIZE > sheet.getWidth() || sy + TILE_SIZE > sheet.getHeight()) return;
            g2.drawImage(sheet,
                x, y, x + TILE_SIZE, y + TILE_SIZE,
                sx, sy, sx + TILE_SIZE, sy + TILE_SIZE,
                null);
        }

        private static BufferedImage loadImage(String assetRelativePath) {
            Path path = resolveAssetPath(assetRelativePath);
            try {
                return ImageIO.read(path.toFile());
            } catch (IOException e) {
                throw new IllegalStateException("Failed to load asset " + path.toAbsolutePath(), e);
            }
        }

        private static Path resolveAssetPath(String assetRelativePath) {
            List<Path> candidates = List.of(
                Paths.get("assets", assetRelativePath),
                Paths.get("PlanetInfo", "Java", "assets", assetRelativePath)
            );
            for (Path candidate : candidates) {
                if (Files.exists(candidate)) {
                    return candidate;
                }
            }
            throw new IllegalStateException("Missing asset " + assetRelativePath + ". Tried: " + candidates);
        }

        private static int wrap(int value, int size) {
            int result = value % size;
            return result < 0 ? result + size : result;
        }

        private static double wrapDouble(double value, int size) {
            double wrapped = value % size;
            return wrapped < 0 ? wrapped + size : wrapped;
        }

        @FunctionalInterface
        private interface TerrainPredicate {
            boolean matches(PlanetGeneration.TerrainType terrainType);
        }
    }
}
