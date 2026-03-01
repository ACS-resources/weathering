# Weathering Addon/Mod Standardization Manual (Draft)

> Scope: this document analyzes the **main game project structure** and proposes a standardized architecture for **addon-based mods**.
> 
> Explicitly excluded from implementation scope: the PlanetInfo Python tool itself (`PlanetInfo/planet_info.py`).

## 1) Current project structure research (what exists now)

## 1.1 Top-level architecture

The repository is currently a classic Unity project, with these key roots:

- `Assets/Game`: gameplay domain code (tiles, industry, logistics, economy, universe maps, etc.).
- `Assets/Scripts/Core`: engine-level runtime systems (save/load, map view, concepts/attributes, UI, globals, refs/values/inventory).
- `Assets/GameEntry`: startup and global game configuration.
- `Assets/Scenes`, `Assets/Tiles`, `Assets/Sprites`, `Assets/Text`: content assets.
- `PlanetInfo`: standalone gameplay-info utility and documentation.
- `DesignDoc`: historical Chinese design/dev documents.

## 1.2 Runtime control model

The runtime is singleton-driven and scene-composed:

- `GameEntry` is the central entry point and map switching coordinator.
- `DataPersistence`, `Globals`, `AttributesPreprocessor`, `MapView`, `UI`, `Sound`, `Localization` are initialized as scene-level systems.
- Map identity and navigation use string map keys in the format `<Type.FullName>#=x,y=...`.

This design is practical and productive for a single codebase, but has weak boundaries for external addons.

## 1.3 Data model primitives

The game state is built from reusable primitives:

- `IValue`/`IValues`: typed scalar progress/value records.
- `IRef`/`IRefs`: typed relationship channels (input/output/link semantics).
- `IInventory`: quantity/type-cap constrained inventory model.
- `IMap`/`IMapDefinition` and `ITile`/`ITileDefinition`: runtime map/tile abstractions.

These are good foundations for addon APIs because they are already interface-oriented.

## 1.4 Content/classification model

Gameplay taxonomy is type-driven:

- Concept marker classes (e.g., `Food`, `Worker`, action/status tags) are annotated with `[Concept]`.
- Construction/economy dependencies use attributes like `[Depend(...)]`, `[ConstructionCostBase(...)]`, etc.
- Many tiles derive from shared bases such as `StandardTile` and `AbstractFactoryStatic`.

This reflection-friendly pattern is highly extensible, but today it assumes all types are in one compilation unit.

## 1.5 Main mod-hosting blockers in current form

1. **Type resolution is string/reflection heavy and global** (`Type.GetType`, `Activator.CreateInstance`).
2. **Assembly scanning is local to executing assembly** (`Assembly.GetExecutingAssembly` in attribute preprocessing).
3. **No explicit module boundary** (no `.asmdef` partitioning / no manifest-based content registration).
4. **Save format binds directly to CLR full names**, making renaming and external package versioning risky.
5. **No lifecycle contract for external modules** (load order, dependency graph, feature flags, compatibility checks).

---

## 2) Standardization goal for addon-based mods

Build a **stable extension contract** where mods can add maps, tiles, concepts, recipes, and UI hooks without patching core game files.

### Target properties

- Backward-compatible save/load.
- Deterministic module load order.
- Clear API vs implementation boundaries.
- Soft-failure behavior (disable one broken mod, keep game bootable).
- Versioned manifests with dependency constraints.

---

## 3) Proposed standardized architecture

## 3.1 Split code into modules via asmdef

Create explicit assembly boundaries:

- `Weathering.Core` (interfaces, base primitives, serialization contracts, registries)
- `Weathering.Runtime` (entry, scene wiring, UI runtime, map runtime)
- `Weathering.Content.BaseGame` (current vanilla content)
- `Weathering.ModKit` (SDK helpers, templates, validation)

Then each addon ships as:

- `Weathering.Mod.<ModName>` assembly (+ optional assets bundle/addressables group)

## 3.2 Introduce a central registry layer (replace free reflection lookup)

Add registries in `Weathering.Core`:

- `TypeRegistry` (stable IDs ↔ runtime `Type`)
- `TileRegistry` (tile IDs, constructors, metadata)
- `MapRegistry` (map IDs, constructors, parent/child rules)
- `ConceptRegistry` (concept IDs + tags)

### Rule

Never serialize raw `Type.FullName` as canonical ID for modded content.
Use a **stable string ID**:

- `mod_id:category/name`
- examples:
  - `base:tile/farm`
  - `base:concept/food`
  - `myexpansion:tile/quantum_refinery`

## 3.3 Add manifest-based module contract

Each mod includes `mod.json`:

```json
{
  "id": "myexpansion",
  "name": "My Expansion",
  "version": "1.2.0",
  "gameVersion": ">=0.5.0 <0.7.0",
  "dependencies": [
    { "id": "base", "version": ">=0.5.0" }
  ],
  "entryType": "MyExpansion.ModEntry",
  "content": {
    "tiles": ["myexpansion:tile/quantum_refinery"],
    "maps": ["myexpansion:map/dyson_cluster"]
  }
}
```

Load pipeline:

1. Discover manifests.
2. Build dependency DAG.
3. Resolve compatible set.
4. Initialize modules in topological order.
5. Register content into registries.
6. Start game.

## 3.4 Define addon lifecycle interface

```csharp
public interface IGameMod
{
    void OnPreRegister(IModContext context);
    void OnRegisterContent(IContentRegistry registry);
    void OnPostRegister(IModContext context);
    void OnGameStart(IGameRuntime runtime);
}
```

This prevents static side effects and gives deterministic lifecycle hooks.

## 3.5 Standardize save schema for moddable content

### Current risk

Saved map/tile records store runtime class names, tightly coupling data to C# symbol names.

### Proposed schema

- Save `type_id` + `schema_version` + payload.
- Keep migration hooks per content type:
  - `IMigratableSaveData.Migrate(fromVersion, toVersion, json)`
- Maintain alias table for renamed IDs.

## 3.6 Standardize content declaration model

Support two equivalent paths:

1. **Code-first declaration** (C# classes register definitions).
2. **Data-first declaration** (JSON/YAML definitions resolved by shared factories).

Recommended for scale: hybrid model.

- behavior in C# (custom logic)
- numbers/tuning/localization/sprite mapping in data files

## 3.7 Standardize localization/assets for mods

Per-mod structure:

- `Localization/en.json`, `Localization/zh-CN.json`
- `Sprites/...`
- `Audio/...`
- `Tiles/...`

All keys should be namespaced with mod ID:

- `myexpansion.tile.quantum_refinery.name`

## 3.8 Compatibility and safety policy

- API surface versioning: `IModApi v1`, `v2`...
- Capability flags (e.g., `requires_map_hooks`, `requires_ui_overlay`).
- Sandboxed failure: if one mod fails registration, show diagnostics and continue with others.
- Deterministic conflict resolution:
  - same ID registered twice -> hard error unless explicit override policy.

---

## 4) Practical migration plan (incremental, low risk)

## Phase 1: Stabilize identifiers

- Add `ContentIdAttribute("base:tile/farm")` to all built-in mod-eligible types.
- Introduce `TypeRegistry` with fallback to old `Type.FullName` for legacy saves.

## Phase 2: Extract Core API

- Move interfaces (`IMap`, `ITile`, `IValue`, `IRef`, etc.) into `Weathering.Core` assembly.
- Ensure runtime/content assemblies depend on Core only.

## Phase 3: Module loader + manifest

- Implement manifest discovery and dependency resolver.
- Add boot diagnostics UI panel for module load reports.

## Phase 4: Save schema v2

- Write `type_id`-based save records.
- Add migration path from legacy save format.

## Phase 5: Official ModKit

- Provide template repo + example mod + CI checks.
- Publish “minimum supported mod API” policy.

---

## 5) Suggested repository standard after migration

```text
Assets/
  Scripts/
    Core/                      # stable APIs + registries + serialization contracts
    Runtime/                   # scene runtime and game loop wiring
    ModKit/                    # public SDK helper classes
  Content/
    BaseGame/                  # vanilla content (maps/tiles/recipes/concepts)
  Mods/
    MyExpansion/
      mod.json
      Scripts/
      Localization/
      Sprites/
      Audio/
```

This reduces coupling between runtime framework and content packs.

---

## 6) Development manual for addon authors (proposed)

## 6.1 Build a new addon

1. Create `Assets/Mods/<ModName>/`.
2. Add asmdef: `Weathering.Mod.<ModName>`.
3. Add `mod.json` with `id`, `version`, dependencies, `entryType`.
4. Implement `IGameMod` entry class.
5. Register concepts, tiles, maps via registry APIs.
6. Add localization and sprite/audio assets under mod folder.
7. Run validator and boot test scene.

## 6.2 Required coding conventions

- Every exported content type must define a unique stable ID.
- Do not hardcode references to concrete vanilla classes when interface-based API exists.
- Do not perform registration in static constructors.
- Treat save payload as versioned contract.

## 6.3 Testing checklist for addon

- Fresh game boot with only this mod enabled.
- Boot with dependency mods enabled.
- Save/load roundtrip on all custom maps/tiles.
- Removal behavior test (disabled/missing mod and fallback messaging).
- Localization fallback test (missing key -> English/default).

## 6.4 Versioning policy for addon developers

- `MAJOR`: breaking save/API changes.
- `MINOR`: new backward-compatible content/features.
- `PATCH`: bug fixes / balance only.

## 6.5 Release checklist

- Manifest valid and schema-compliant.
- No duplicate IDs.
- All user-facing strings localized.
- Save migration tests passing.
- Changelog written.

---

## 7) Immediate next actions for this repository

1. Add a lightweight `TypeRegistry` abstraction and route new code through it.
2. Add `ContentIdAttribute` for built-in maps/tiles/concepts incrementally.
3. Refactor attribute preprocessing to scan registered assemblies/modules instead of only executing assembly.
4. Introduce `mod.json` parser and dependency resolver (even before external distribution).
5. Add a `Mods` runtime diagnostics panel (loaded/failed modules + reasons).

These five actions deliver the fastest path from current monolith to addon-ready architecture without rewriting gameplay logic.
