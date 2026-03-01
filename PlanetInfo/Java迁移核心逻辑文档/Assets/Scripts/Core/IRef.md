# IRef.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/IRef.cs`
- 命名空间：`Weathering`
- 代码行数：`95`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `interface IRef`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class RefData`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Ref`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `public ToData(IRef r)`
- `public FromData(RefData rData)`
- `public Create(Type base_type,
            Type type,
            long base_value,
            long value,

            Type left, 
            Type right, 
            long x, 
            long y)`

### 3.2 属性签名

- `public IRef`
- `public RefData`
- `public BaseType`
- `public Type`
- `public BaseValue`
- `public Value`
- `public Left`
- `public Right`
- `public X`
- `public Y`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;

namespace Weathering
{
    public interface IRef
    {
        Type Type { get; set; }
        // Type BaseType { get; set; }

        long Value { get; set; }
        long BaseValue { get; set; }

        Type Left { get; set; }
        Type Right { get; set; }
        long X { get; set; }
        long Y { get; set; }
    }

    public class RefData
    {
        public string base_type;
        public string type;
        public long base_val;
        public long val;
        public string left;
        public string right;
        public long x;
        public long y;
    }

    public class Ref : IRef
    {
        public Type BaseType { get; set; } = null;
        public Type Type { get; set; } = null;
        public long BaseValue { get; set; } = 0;
        public long Value { get; set; } = 0;

        public Type Left { get; set; } = null;
        public Type Right { get; set; } = null;
        public long X { get; set; } = 0;
        public long Y { get; set; } = 0;

        public static RefData ToData(IRef r) {
            return new RefData {
                // base_type = r.BaseType.FullName,
                type = r.Type?.FullName,
                base_val = r.BaseValue,
                val = r.Value,

                left = r.Left?.FullName,
                right = r.Right?.FullName,
                x = r.X,
                y = r.Y,
            };
        }
        public static IRef FromData(RefData rData) {
            return Create(
                rData.base_type == null ? null : Type.GetType(rData.base_type),
                rData.type == null ? null : Type.GetType(rData.type),
                rData.base_val,
                rData.val,
                rData.left == null ? null : Type.GetType(rData.left), 
                rData.right == null ? null : Type.GetType(rData.right),
                rData.x, 
                rData.y
                );
        }

        public static Ref Create(
            Type base_type,
            Type type,
            long base_value,
            long value,

            Type left, 
            Type right, 
            long x, 
            long y
            ) {
            return new Ref {
                BaseType = base_type,
                Type = type,
                BaseValue = base_value,
                Value = value,

                Left = left,
                Right = right,
                X = x,
                Y = y,
            };
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