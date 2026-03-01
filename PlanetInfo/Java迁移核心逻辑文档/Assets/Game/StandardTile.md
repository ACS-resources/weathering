# StandardTile.cs（Java 迁移解构文档）

- 源文件：`Assets/Game/StandardTile.cs`
- 命名空间：`Weathering`
- 代码行数：`91`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `class StandardTile`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `public SetValues(IValues values)`
- `public SetRefs(IRefs refs)`
- `public SetInventory(IInventory inventory)`
- `public SetInventoryOfSupply(IInventory inventory)`
- `public GetMap()`
- `public GetPos()`
- `public GetTileHashCode()`
- `public CanConstruct()`
- `public CanDestruct()`
- `public OnEnable()`
- `public OnConstruct(ITile oldTile)`
- `public OnDestruct(ITile newTile)`
- `public OnTap()`
- `public OnTapPlaySound()`
- `public OnDestructWithMap()`

### 3.2 属性签名

- `public NeedUpdateSpriteKeys`
- `public NeedUpdateSpriteKeysPositionX`
- `public NeedUpdateSpriteKeysPositionY`
- `public Values`
- `public Refs`
- `public Inventory`
- `public InventoryOfSupply`
- `public Map`
- `public Pos`
- `public TileHashCode`
- `public SpriteKeyRoad`
- `public SpriteKey`
- `public SpriteKeyHighLight`
- `public SpriteKeyOverlay`
- `public SpriteLeft`
- `public SpriteRight`
- `public SpriteUp`
- `public SpriteDown`
- `public TileSpriteKeyBedrockBuffer`
- `public TileSpriteKeyWaterBuffer`
- `public TileSpriteKeyGrassBuffer`
- `public TileSpriteKeyTreeBuffer`
- `public TileSpriteKeyHillBuffer`
- `public TileSpriteKeyRoadBuffer`
- `public TileSpriteKeyLeftBuffer`
- `public TileSpriteKeyRightBuffer`
- `public TileSpriteKeyUpBuffer`
- `public TileSpriteKeyDownBuffer`
- `public TileSpriteKeyBuffer`
- `public TileSpriteKeyHighLightBuffer`
- `public TileSpriteKeyOverlayBuffer`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Weathering
{
    /// <summary>
    /// StandardTile功能
    /// 1. ISavable, Values, Refs, Inventory
    /// 2. Map, Pos, HashCode
    /// 3. SpriteKey
    /// 4. Construct, Destruct, Enable
    /// </summary>
    public abstract class StandardTile : ITileDefinition
    {
        public bool NeedUpdateSpriteKeys { get; set; } = true;
        public int NeedUpdateSpriteKeysPositionX { get; set; }
        public int NeedUpdateSpriteKeysPositionY { get; set; }

        public IValues Values { get; protected set; } = null;
        public void SetValues(IValues values) => Values = values;
        public IRefs Refs { get; set; } = null;
        public void SetRefs(IRefs refs) => Refs = refs;
        public IInventory Inventory { get; protected set; }
        public void SetInventory(IInventory inventory) => Inventory = inventory;
        public IInventory InventoryOfSupply { get => throw new NotImplementedException(); protected set => throw new NotImplementedException(); }
        public void SetInventoryOfSupply(IInventory inventory) => throw new NotImplementedException(); // InventoryOfSupply = inventory;


        public IMap Map { get; set; }
        public Vector2Int Pos { get; set; }
        public IMap GetMap() => Map;
        public Vector2Int GetPos() => Pos;
        public uint TileHashCode { get; set; }
        public uint GetTileHashCode() => TileHashCode;


        /// <summary>
        /// SpriteKeyBackground和SpriteKeyBase都是Map定义的
        /// </summary>
        protected virtual bool PreserveLandscape => true;
        public virtual string SpriteKeyBedrock => Map.GetSpriteKeyBedrock(Pos);
        public virtual string SpriteKeyWater => Map.GetSpriteKeyWater(Pos);
        public virtual string SpriteKeyGrass => PreserveLandscape ? Map.GetSpriteKeyGrass(Pos) : null;
        public virtual string SpriteKeyTree => PreserveLandscape ? Map.GetSpriteKeyTree(Pos) : null;
        public virtual string SpriteKeyHill => PreserveLandscape ? Map.GetSpriteKeyHill(Pos) : null;

        public virtual string SpriteKeyRoad { get => null; }
        public virtual string SpriteKey { get => null; } // 
        public virtual string SpriteKeyHighLight { get => null; } // 
        public virtual string SpriteKeyOverlay { get => null; } // 用于指示标记

        public virtual string SpriteLeft { get => null; }
        public virtual string SpriteRight { get => null; }
        public virtual string SpriteUp { get => null; }
        public virtual string SpriteDown { get => null; }

        public Tile TileSpriteKeyBedrockBuffer { get; set; }
        public Tile TileSpriteKeyWaterBuffer { get; set; }
        public Tile TileSpriteKeyGrassBuffer { get; set; }
        public Tile TileSpriteKeyTreeBuffer { get; set; }
        public Tile TileSpriteKeyHillBuffer { get; set; }
        public Tile TileSpriteKeyRoadBuffer { get; set; }
        public Tile TileSpriteKeyLeftBuffer { get; set; }
        public Tile TileSpriteKeyRightBuffer { get; set; }
        public Tile TileSpriteKeyUpBuffer { get; set; }
        public Tile TileSpriteKeyDownBuffer { get; set; }
        public Tile TileSpriteKeyBuffer { get; set; }
        public Tile TileSpriteKeyHighLightBuffer { get; set; }
        public Tile TileSpriteKeyOverlayBuffer { get; set; }


        public virtual bool CanConstruct() => true;
        public virtual bool CanDestruct() => false;

        public virtual void OnEnable() { }
        public virtual void OnConstruct(ITile oldTile) { }
        public virtual void OnDestruct(ITile newTile) { }
        public abstract void OnTap();
        public virtual void OnTapPlaySound() {
            Sound.Ins.PlayDefaultSound();
        }

        public virtual void OnDestructWithMap() {
            
        }
    }
}

```

## 5. Java 迁移建议（本文件）

1. 先保留领域模型（类/接口）结构，再替换底层平台调用。
2. 若含 Unity API（如 `MonoBehaviour`、`Vector2Int`、`Tile`），先在 Java 中定义适配层接口与数据类。
3. 对外部可序列化字段保持字段语义与默认值一致，避免存档语义漂移。
4. 对反射型逻辑优先替换为“注册表 + 稳定 content_id”机制。
5. 将该文件纳入跨语言黄金样例测试，确保行为可回归。