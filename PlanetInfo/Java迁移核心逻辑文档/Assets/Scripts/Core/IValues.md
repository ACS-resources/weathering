# IValues.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/IValues.cs`
- 命名空间：`Weathering`
- 代码行数：`117`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `interface IValues`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Values`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `public FromData(Dictionary<string, ValueData> data)`
- `public GetOne()`
- `public Get(Type type)`
- `public Create(Type type)`
- `public GetOrCreate(Type type)`
- `public Has(Type type)`
- `public Remove(Type type)`

### 3.2 属性签名

- `public IValues`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;

namespace Weathering
{
    public interface IValues
    {
        IValue Create(Type type);
        IValue GetOrCreate(Type type);
        IValue Get(Type type);
        bool Has(Type type);
        bool Remove(Type type);

        IValue Create<T>();
        IValue GetOrCreate<T>();
        IValue Get<T>();
        bool Has<T>();
        bool Remove<T>();

        Dictionary<Type, IValue> Dict { get; }
    }

    public class Values : IValues
    {
        private Values() { }

        public Dictionary<Type, IValue> Dict { get; private set; } = null;

        public static Dictionary<string, ValueData> ToData(IValues values) {
            if (values == null) return null;
            Dictionary<string, ValueData> dict = new Dictionary<string, ValueData>();
            foreach (var pair in values.Dict) {
                dict.Add(pair.Key.FullName, Value.ToData(pair.Value));
            }
            return dict;
        }
        public static IValues FromData(Dictionary<string, ValueData> data) {
            if (data == null) return null;
            IValues result = GetOne();
            foreach (var pair in data) {
                Type type = Type.GetType(pair.Key);
                IValue value = Value.FromData(pair.Value);
                result.Dict.Add(type, value);
            }
            return result;
        }


        public static IValues GetOne() {
            return new Values {
                Dict = new Dictionary<Type, IValue>()
            };
        }

        public IValue Get(Type type) {
            if (Dict.TryGetValue(type, out IValue value)) {
                return value;
            } else {
                throw new Exception(type.Name);
            }
        }
        public IValue Get<T>() {
            return Get(typeof(T));
        }

        public IValue Create(Type type) {
            if (Dict.TryGetValue(type, out IValue value)) {
                throw new Exception();
            } else {
                value = Value.Create(0, 0, 0, 0, 0, TimeUtility.GetTicks());
                Dict.Add(type, value);
                return value;
            }
        }
        public IValue Create<T>() {
            return Create(typeof(T));
        }

        public IValue GetOrCreate(Type type) {
            if (Dict.TryGetValue(type, out IValue value)) {
                return value;
            } else {
                value = Value.Create(0, 0, 0, 0, 0, TimeUtility.GetTicks());
                Dict.Add(type, value);
                return value;
            }
        }
        public IValue GetOrCreate<T>() {
            return GetOrCreate(typeof(T));
        }

        public bool Has(Type type) {
            if (Dict.TryGetValue(type, out IValue value)) {
                return true;
            } else {
                return false;
            }
        }
        public bool Has<T>() {
            return Has(typeof(T));
        }

        public bool Remove(Type type) {
            if (Dict.ContainsKey(type)) {
                Dict.Remove(type);
                return true;
            }
            return false;
        }

        public bool Remove<T>() {
            return Remove(typeof(T));
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