# IMap.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/IMap.cs`
- 命名空间：`Weathering`
- 代码行数：`85`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `interface ISavable`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `interface ISavableDefinition`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `interface IMap`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `interface IMapDefinition`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.2 属性签名

- `public ISavable`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;

namespace Weathering
{
    public interface ISavable
    {
        IValues Values { get; }
        IRefs Refs { get; }
        IInventory Inventory { get; }
        IInventory InventoryOfSupply { get; }
    }

    public interface ISavableDefinition : ISavable
    {
        void SetValues(IValues values);
        void SetRefs(IRefs refs);
        void SetInventory(IInventory inventory);
        void SetInventoryOfSupply(IInventory inventory);
    }

    public interface IMap : ISavable
    {
        int Width { get; }
        int Height { get; }
        bool ControlCharacter { get; }

        string GetMapKey { get; }
        ITile ParentTile { get; }
        void EnterParentMap();
        void EnterChildMap(Vector2Int pos);


        // 目前有两种方案定义DefaultTileType, 目前采用DefaultTileType够用
        // Type GenerateTileType(Vector2Int pos);
        Type DefaultTileType { get; }

        string GetSpriteKeyBedrock(Vector2Int pos);
        string GetSpriteKeyWater(Vector2Int pos);
        string GetSpriteKeyGrass(Vector2Int pos);
        string GetSpriteKeyTree(Vector2Int pos);
        string GetSpriteKeyHill(Vector2Int pos);


        bool CanUpdateAt<T>(Vector2Int pos);
        bool CanUpdateAt(Type type, Vector2Int pos);
        bool CanUpdateAt<T>(int i, int j);
        bool CanUpdateAt(Type type, int i, int j);


        ITile Get(int i, int j);
        ITile Get(Vector2Int pos);


        T UpdateAt<T>(ITile oldTile) where T : class, ITile;
        ITile UpdateAt(Type type, ITile oldTile);
    }

    public interface IMapDefinition : IMap, ISavableDefinition
    {

        Vector2Int ParentPositionBuffer { get; set; }

        string MapKey { get; set; }

        uint HashCode { get; set; }
        void SetTile(Vector2Int pos, ITileDefinition tile, bool inConstruction=false);
        void OnEnable();
        void OnDisable();
        void OnConstruct();
        void AfterConstructMapBody();

        ITileDefinition GetTileFast(int i, int j);

        // void AfterGeneration();

        void OnTapTile(ITile tile);

        bool CanDelete { get; }
        void Delete();
    }
}

```

## 5. Java 迁移建议（本文件）

1. 先保留领域模型（类/接口）结构，再替换底层平台调用。
2. 若含 Unity API（如 `MonoBehaviour`、`Vector2Int`、`Tile`），先在 Java 中定义适配层接口与数据类。
3. 对外部可序列化字段保持字段语义与默认值一致，避免存档语义漂移。
4. 对反射型逻辑优先替换为“注册表 + 稳定 content_id”机制。
5. 将该文件纳入跨语言黄金样例测试，确保行为可回归。