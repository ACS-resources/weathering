package com.weathering.generation;

public final class Hashing {
    private Hashing() {}

    public static long hash32(long a) {
        long v = a & 0xFFFFFFFFL;
        v = (v ^ 61L) ^ (v >>> 16);
        v = (v + (v << 3)) & 0xFFFFFFFFL;
        v = v ^ (v >>> 4);
        v = (v * 0x27d4eb2dL) & 0xFFFFFFFFL;
        v = v ^ (v >>> 15);
        return v & 0xFFFFFFFFL;
    }

    public static long hashString(String value) {
        long result = 7L;
        for (int i = 0; i < value.length(); i++) {
            result = (result + value.charAt(i)) & 0xFFFFFFFFL;
            result = hash32(result);
        }
        return result & 0xFFFFFFFFL;
    }

    public static long hash(int i, int j, int width, int height, int offset) {
        long seed = ((long) offset * width + height + i + (long) j * width) & 0xFFFFFFFFL;
        return hash32(seed);
    }

    public static long addSalt(long a, long salt) {
        return hash32((a + salt) & 0xFFFFFFFFL);
    }

    public static long hashed(UIntRef value) {
        value.value = hash32(value.value);
        return value.value;
    }

    public static Vec2 randomVec2Simple(int i, int j, int width, int height, int offset) {
        int x = i % width;
        if (x < 0) x += width;
        int y = j % height;
        if (y < 0) y += height;

        long hash = hash(x, y, width, height, offset);
        return switch ((int) (hash % 4)) {
            case 0 -> new Vec2(-1f, 1f);
            case 1 -> new Vec2(-1f, -1f);
            case 2 -> new Vec2(1f, 1f);
            case 3 -> new Vec2(1f, -1f);
            default -> throw new IllegalStateException();
        };
    }

    public static float perlinNoise(float x, float y, int width, int height, int layer) {
        int p0x = (int) x;
        int p0y = (int) y;
        int p1x = p0x;
        int p1y = p0y + 1;
        int p2x = p0x + 1;
        int p2y = p0y + 1;
        int p3x = p0x + 1;
        int p3y = p0y;

        Vec2 g0 = randomVec2Simple(p0x, p0y, width, height, layer);
        Vec2 g1 = randomVec2Simple(p1x, p1y, width, height, layer);
        Vec2 g2 = randomVec2Simple(p2x, p2y, width, height, layer);
        Vec2 g3 = randomVec2Simple(p3x, p3y, width, height, layer);

        float v0x = x - p0x;
        float v0y = y - p0y;
        float v1x = x - p1x;
        float v1y = y - p1y;
        float v2x = x - p2x;
        float v2y = y - p2y;
        float v3x = x - p3x;
        float v3y = y - p3y;

        float product0 = g0.x * v0x + g0.y * v0y;
        float product1 = g1.x * v1x + g1.y * v1y;
        float product2 = g2.x * v2x + g2.y * v2y;
        float product3 = g3.x * v3x + g3.y * v3y;

        float d0 = fade(x - p0x);
        float n0 = product1 * (1.0f - d0) + product2 * d0;
        float n1 = product0 * (1.0f - d0) + product3 * d0;

        float d1 = fade(y - p0y);
        return n1 * (1.0f - d1) + n0 * d1;
    }

    private static float fade(float t) {
        return t * t * t * (t * (t * 6 - 15) + 10);
    }

    public static final class UIntRef { public long value; public UIntRef(long value) { this.value = value & 0xFFFFFFFFL; } }
    public record Vec2(float x, float y) {}
}
