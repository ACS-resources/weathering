package com.weathering.mapped;

import com.weathering.generation.Hashing;
import com.weathering.generation.PlanetGeneration;

/**
 * Ported constants and startup wiring from original MapOfPlanet.cs.
 * Keeps map-key/hash based generation in a non-Unity runtime.
 */
public final class MappedPlanetGeneration {
    private MappedPlanetGeneration() {}

    // Original startup chain used across migration checks.
    public static final String PRIMARY_PLANET_MAP_KEY = "Weathering.MapOfPlanet#=1,4=14,93=24,31";
    public static final String PRIMARY_PLANET_SELF_INDEX = "#=1,4=14,93=24,31";

    // Original landing position from MapOfPlanet.AfterConstructMapBody()
    public static final int LANDING_X = 4;
    public static final int LANDING_Y = 83;

    // Original RandomSeed in MapOfPlanet
    public static final int PLANET_RANDOM_SEED = 5;

    public static PlanetGeneration.PlanetMap generatePrimaryPlanet() {
        long mapHash = Hashing.hashString(PRIMARY_PLANET_MAP_KEY);
        long selfHash = Hashing.hashString(PRIMARY_PLANET_SELF_INDEX);
        return PlanetGeneration.generate(mapHash, selfHash, PLANET_RANDOM_SEED);
    }
}
