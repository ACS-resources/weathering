# Res.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/ResConfig/Res.cs`
- 命名空间：`Weathering`
- 代码行数：`87`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `interface IRes`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Res`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `public TryGetTile(string name, out Tile result)`
- `public TryGetSprite(string name)`
- `private Awake()`
- `private ProcessObject(Transform trans)`

### 3.2 属性签名

- `public IRes`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Weathering
{
    public interface IRes
    {
        // Tile GetTile(string name);
        bool TryGetTile(string name, out Tile result); // 这种形式便于判断
        // Sprite GetSprite(string name);
        Sprite TryGetSprite(string name); // 这种形式便于直接返回null
    }

    public class Res : MonoBehaviour, IRes
    {
        public static IRes Ins;

        [SerializeField]
        private Tile EmptyTilePrefab;

        private Dictionary<string, Sprite> staticSprites = new Dictionary<string, Sprite>();
        private Dictionary<string, Tile> staticTiles = new Dictionary<string, Tile>();
        //public Tile GetTile(string name) {
        //    if (staticTiles.TryGetValue(name, out Tile result)) {
        //        return result;
        //    }
        //    throw new Exception("No Tile called: " + name + ".  Total: " + staticTiles.Count);
        //}
        public bool TryGetTile(string name, out Tile result) {
            if (staticTiles.TryGetValue(name, out Tile result2)) {
                result = result2;
                return true;
            } else if (staticSprites.TryGetValue(name, out Sprite result3)) {
                Tile tile = Instantiate(EmptyTilePrefab);
                tile.sprite = result3;
                result = tile;

                staticTiles.Add(name, tile);
                return true;
            }
            result = null;
            return false;
        }

        //public Sprite GetSprite(string name) {
        //    if (staticSprites.TryGetValue(name, out Sprite result)) {
        //        return result;
        //    }
        //    throw new Exception("No Sprite called: " + name);
        //}
        public Sprite TryGetSprite(string name) {
            if (staticSprites.TryGetValue(name, out Sprite result)) {
                return result;
            }
            return null;
        }

        private void Awake() {
            if (Ins != null) throw new System.Exception();
            Ins = this;
            foreach (Transform item in transform) {
                ProcessObject(item);
                foreach (Transform item2 in item) {
                    ProcessObject(item2);
                    foreach (Transform item3 in item2) {
                        ProcessObject(item3);
                    }
                }
            }
        }

        private void ProcessObject(Transform trans) {
            SpriteResContainer spriteContainer = trans.GetComponent<SpriteResContainer>();
            if (spriteContainer != null) {
                if (spriteContainer.Sprites == null) {
                    throw new Exception($"{spriteContainer.name} 没用配置内容");
                }
                foreach (var sprite in spriteContainer.Sprites) {
                    staticSprites.Add(sprite.name, sprite);
                }
            }
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