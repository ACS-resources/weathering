# CharacterView.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/Map/CharacterView.cs`
- 命名空间：`Weathering`
- 代码行数：`68`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `class CharacterView`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `private Awake()`
- `public SetCharacterSprite(Vector2Int direction, bool moving)`

### 3.2 属性签名

- `public Ins`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Experimental.Rendering.Universal;

namespace Weathering
{
    public class CharacterView : MonoBehaviour
    {
        public Sprite DefaultSprite;

        //public Transform FlashLightTransform;

        //public Light2D FlashLight;

        public Sprite[] TestSprites;

        public CharacterView Ins { get; private set; }

        private SpriteRenderer sr;
        private void Awake() {
            if (Ins != null) throw new Exception();
            Ins = this;

            sr = GetComponent<SpriteRenderer>();
            if (sr == null) throw new Exception();
        }

        private bool movingLast = false;
        private Vector2Int directionLast = Vector2Int.zero;

        private Vector3 lightVelocity = Vector3.zero;

        public float Distance = 2f;
        public void SetCharacterSprite(Vector2Int direction, bool moving) {

            bool needUpdateFlashLight = moving != movingLast || direction != directionLast;

            if (moving || needUpdateFlashLight) {
                int index;

                if (direction == Vector2Int.down) {
                    index = 0;
                } else if (direction == Vector2Int.left) {
                    index = 1;
                } else if (direction == Vector2Int.right) {
                    index = 2;
                } else if (direction == Vector2Int.up) {
                    index = 3;
                } else {
                    index = 0;
                }

                index *= 4;

                if (moving) index += TimeUtility.GetSimpleFrame(0.125f, 4);

                directionLast = direction;
                movingLast = moving;

                sr.sprite = TestSprites[index];
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