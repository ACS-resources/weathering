# ITile.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/ITile.cs`
- 命名空间：`Weathering`
- 代码行数：`80`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `interface ITile`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `interface ITileDefinition`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

- 当前文件无明显方法/属性签名（可能是常量、标记类型或注释占位）。

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Weathering
{
    public interface ITile : ISavable
    {
        void OnTap();
        void OnTapPlaySound();

        bool NeedUpdateSpriteKeys { get; set; }

        // bool CanConstruct();
        bool CanDestruct();

        IMap GetMap();
        Vector2Int GetPos();
        uint GetTileHashCode();
    }

    public interface ITileDefinition : ITile, ISavableDefinition
    {
        int NeedUpdateSpriteKeysPositionX { get; set; }
        int NeedUpdateSpriteKeysPositionY { get; set; }


        string SpriteKeyBedrock { get; }
        Tile TileSpriteKeyBedrockBuffer { get; set; }
        string SpriteKeyWater { get; }
        Tile TileSpriteKeyWaterBuffer { get; set; }
        string SpriteKeyGrass { get; }
        Tile TileSpriteKeyGrassBuffer { get; set; }
        string SpriteKeyTree { get; }
        Tile TileSpriteKeyTreeBuffer { get; set; }
        string SpriteKeyHill { get; }
        Tile TileSpriteKeyHillBuffer { get; set; }
        string SpriteKeyRoad { get; }
        Tile TileSpriteKeyRoadBuffer { get; set; }

        string SpriteLeft { get; }
        Tile TileSpriteKeyLeftBuffer { get; set; }
        string SpriteRight { get; }
        Tile TileSpriteKeyRightBuffer { get; set; }
        string SpriteUp { get; }
        Tile TileSpriteKeyUpBuffer { get; set; }
        string SpriteDown { get; }
        Tile TileSpriteKeyDownBuffer { get; set; }

        string SpriteKey { get; }
        Tile TileSpriteKeyBuffer { get; set; }
        string SpriteKeyHighLight { get; }
        Tile TileSpriteKeyHighLightBuffer { get; set; }
        string SpriteKeyOverlay { get; }
        Tile TileSpriteKeyOverlayBuffer { get; set; }

        IMap Map { get; set; }
        UnityEngine.Vector2Int Pos { get; set; }
        uint TileHashCode { get; set; }

        void OnConstruct(ITile oldTile);
        void OnDestruct(ITile newTile);

        void OnDestructWithMap();

        void OnEnable();

    }

}








```

## 5. Java 迁移建议（本文件）

1. 先保留领域模型（类/接口）结构，再替换底层平台调用。
2. 若含 Unity API（如 `MonoBehaviour`、`Vector2Int`、`Tile`），先在 Java 中定义适配层接口与数据类。
3. 对外部可序列化字段保持字段语义与默认值一致，避免存档语义漂移。
4. 对反射型逻辑优先替换为“注册表 + 稳定 content_id”机制。
5. 将该文件纳入跨语言黄金样例测试，确保行为可回归。