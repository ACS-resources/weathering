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
- hierarchy spot-check for `universe(1,4) -> galaxy(14,93) -> star-system body(24,31)`,
- universe galaxy-tile distribution (with sample actual galaxy coordinates),
- galaxy star-system-tile distribution (with sample actual star-system coordinates),
- star-system star positions + celestial body histogram + non-empty body samples (skip `SpaceEmptiness`),
- planet profile + attribute ranges + terrain histogram + sample cells,
- starting-star planet key `Weathering.MapOfPlanet#=1,4=14,93=24,31` with an upside-down landing-centered terrain view around the original landing position `(4,83)`,
- ANSI-colored terrain+ore upside-down landing-centered grid for visual verification,
- compressed coordinate indices for manual tile lookup: top uses `hex*10+dec` (e.g. `A0` => 100, `B6` => 116) and left uses world y values,
- star-system body totals for the known chain (`(1,4)->(14,93)`) including expected `planetLikeBodies=16` and `StarOrange`.

Terrain letters:
- `S` = Sea
- `P` = Plain
- `F` = Forest
- `M` = Mountain

ANSI terrain+ore grid legend:
- `~` aqua = Sea
- `.` green = Plain
- `T` dark green = Forest
- `^` light brown = Mountain
- `C` black = Coal ore (overlay on mountain)
- `I` silver = Iron ore (overlay on mountain)
- `G` gold = Gold ore (overlay on mountain)
- `c` orange = Copper ore (overlay on mountain)
- `B` taupe = Bauxite ore (overlay on mountain)


Parity note: hierarchy checks are kept strict, while the starting planet terrain remains governed by the general terrain algorithm (no hardcoded shape assertions).

## Run map viewer (Swing UI, WASD camera)

This viewer renders the primary planet (`Weathering.MapOfPlanet#=1,4=14,93=24,31`) at the original 16x16 tile scale, with terrain edge textures (4x4 grass rule tile + full original 6x8 mountain rule mapping), mountain ores rendered on top, and supports camera movement with **W/A/S/D** (cycling/wraparound). It resolves assets when launched from either the repository root or `PlanetInfo/Java` directory.

```powershell
cd PlanetInfo/Java
if (!(Test-Path out)) { New-Item -ItemType Directory -Path out | Out-Null }
$files = Get-ChildItem -Recurse src/main/java,src/test/java -Filter *.java | ForEach-Object { $_.FullName }
javac -encoding UTF-8 -d out $files
java -cp out com.weathering.viewer.PlanetMapViewer
```

```cmd
cd PlanetInfo\Java
if not exist out mkdir out
for /r src %f in (*.java) do @echo %f>> sources.txt
javac -encoding UTF-8 -d out @sources.txt
java -cp out com.weathering.viewer.PlanetMapViewer
del sources.txt
```
