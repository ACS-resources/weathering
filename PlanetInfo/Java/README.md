# Java Prototype for Core World Generation

This directory contains a Unity-independent Java prototype for core generation logic, aligned to the original C# rules in:
- `Assets/Game/Universe/MapOfUniverseDefaultTile.cs`
- `Assets/Game/Universe/MapOfGalaxyDefaultTile.cs`
- `Assets/Game/Universe/MapOfStarSystem.cs`
- `Assets/Game/Universe/MapOfStarSystemDefaultTile.cs`
- `Assets/Game/Universe/MapOfPlanet.cs`
- `Assets/Game/StandardMap.cs`
- `Assets/Scripts/Core/RandomnessGenerator/HashUtility.cs`
- `Assets/Scripts/Utility/GeographyUtility/GeographyUtility.cs`

## Scope
- Galaxy tile generation in universe map.
- Star-system tile generation in galaxy map.
- Star position and celestial-body classification in star-system map.
- Planet profile generation (size, mineral density).
- Planet attribute generation (altitude, moisture, temperature) and terrain derivation.

## Structure
- `src/main/java/com/weathering/generation/Hashing.java`:
  C#-compatible hash / perlin-noise building blocks.
- `src/main/java/com/weathering/generation/CelestialGeneration.java`:
  galaxy/star-system/celestial-body rules.
- `src/main/java/com/weathering/generation/PlanetGeneration.java`:
  map attribute generation and terrain derivation.
- `src/test/java/com/weathering/generation/GenerationParityTest.java`:
  executable parity tests for deterministic generation behavior.

## Run checks (Win11 + JDK 21)

### PowerShell
```powershell
cd PlanetInfo/Java
if (!(Test-Path out)) { New-Item -ItemType Directory -Path out | Out-Null }
$files = Get-ChildItem -Recurse src/main/java,src/test/java -Filter *.java | ForEach-Object { $_.FullName }
javac -encoding UTF-8 -d out $files
java -cp out com.weathering.generation.GenerationParityTest
```

### CMD
```cmd
cd PlanetInfo\Java
if not exist out mkdir out
for /r src %f in (*.java) do @echo %f>> sources.txt
javac -encoding UTF-8 -d out @sources.txt
java -cp out com.weathering.generation.GenerationParityTest
del sources.txt
```


## Manual-check output

After compiling, run:

```powershell
java -cp out com.weathering.generation.GenerationManualReport
```

This prints human-checkable reports for:
- universe galaxy-tile distribution,
- galaxy star-system-tile distribution,
- star-system star positions + celestial body histogram,
- planet profile + attribute ranges + terrain histogram + sample cells.
