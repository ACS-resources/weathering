# GlobalVolume.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/GlobalVolume/GlobalVolume.cs`
- 命名空间：`Weathering`
- 代码行数：`47`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `class GlobalVolume`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `private Awake()`

### 3.2 属性签名

- `public Ins`
- `public Volume`
- `public Profile`
- `public WhiteBalance`
- `public Tonemapping`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp


using UnityEngine;

namespace Weathering
{
    public class GlobalVolume : MonoBehaviour
    {
        public static GlobalVolume Ins { get; private set; }

        [SerializeField]
        private UnityEngine.Rendering.Volume volume;
        public UnityEngine.Rendering.Volume Volume { get => volume; }

        public UnityEngine.Rendering.VolumeProfile Profile { get => volume.sharedProfile; }


        private UnityEngine.Rendering.Universal.WhiteBalance whiteBalance = null;
        public UnityEngine.Rendering.Universal.WhiteBalance WhiteBalance {
            get {
                if (whiteBalance == null && Profile.TryGet(out whiteBalance)) {
                }
                if (whiteBalance == null) {
                    throw new System.Exception();
                }
                return whiteBalance;
            }
        }

        private UnityEngine.Rendering.Universal.Tonemapping tonemapping = null;
        public UnityEngine.Rendering.Universal.Tonemapping Tonemapping {
            get {
                if (tonemapping == null && Profile.TryGet(out tonemapping)) {
                }
                if (tonemapping == null) {
                    throw new System.Exception();
                }
                return tonemapping;
            }
        }

        private void Awake() {
            if (Ins != null) throw new System.Exception();
            Ins = this;
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