# IRefs.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/IRefs.cs`
- 命名空间：`Weathering`
- 代码行数：`125`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `interface IRefs`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Refs`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `public FromData(Dictionary<string, RefData> data)`
- `public GetOne()`
- `public Get(Type type)`
- `public TryGet(Type type, out IRef result)`
- `public Create(Type type)`
- `public GetOrCreate(Type type)`
- `public Has(Type type)`
- `public Remove(Type type)`

### 3.2 属性签名

- `public IRefs`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;

namespace Weathering
{
    public interface IRefs
    {
        IRef Create<T>();
        IRef Create(Type type);
        IRef Get<T>();
        IRef Get(Type type);
        IRef GetOrCreate<T>();
        IRef GetOrCreate(Type type);
        void Remove<T>();
        void Remove(Type type);
        bool Has(Type type);
        bool Has<T>();

        bool TryGet<T>(out IRef result);
        bool TryGet(Type type, out IRef result);
        Dictionary<Type, IRef> Dict { get; }
    }

    public class Refs : IRefs
    {
        private Refs() { }
        public Dictionary<Type, IRef> Dict { get; set; } = null;

        public static Dictionary<string, RefData> ToData(IRefs refs) {
            if (refs == null) return null;
            Dictionary<string, RefData> data = new Dictionary<string, RefData>();
            foreach (var pair in refs.Dict) {
                data.Add(pair.Key.FullName, Ref.ToData(pair.Value));
            }
            return data;
        }

        public static IRefs FromData(Dictionary<string, RefData> data) {
            if (data == null) return null;
            IRefs result = GetOne();
            foreach (var pair in data) {
                Type type = Type.GetType(pair.Key);
                IRef value = Ref.FromData(pair.Value);
                result.Dict.Add(type, value);
            }
            return result;
        }

        public static IRefs GetOne() {
            return new Refs {
                Dict = new Dictionary<Type, IRef>()
            };
        }

        public IRef Get<T>() {
            return Get(typeof(T));
        }
        public IRef Get(Type type) {
            if (Dict.TryGetValue(type, out IRef value)) {
                return value;
            } else {
                throw new Exception(type.Name);
            }
        }
        public bool TryGet<T>(out IRef result) {
            return TryGet(typeof(T), out result);
        }
        public bool TryGet(Type type, out IRef result) {
            return Dict.TryGetValue(type, out result);
        }

        public IRef Create<T>() {
            return Create(typeof(T));
        }
        public IRef Create(Type type) {
            if (Dict.TryGetValue(type, out IRef value)) {
                throw new Exception("已有：" + type.FullName);
            } else {
                value = Ref.Create(null, null, 0, 0, null, null, 0, 0);
                Dict.Add(type, value);
                return value;
            }
        }

        public IRef GetOrCreate<T>() {
            return GetOrCreate(typeof(T));
        }
        public IRef GetOrCreate(Type type) {
            if (Dict.TryGetValue(type, out IRef value)) {
                return value;
            } else {
                value = Ref.Create(null, null, 0, 0, null, null, 0, 0);
                Dict.Add(type, value);
                return value;
            }
        }


        public bool Has(Type type) {
            if (Dict.TryGetValue(type, out IRef value)) {
                return true;
            } else {
                return false;
            }
        }
        public bool Has<T>() {
            return Has(typeof(T));
        }


        public void Remove<T>() {
            Remove(typeof(T));
        }
        public void Remove(Type type) {
            if (Dict.ContainsKey(type)) {
                Dict.Remove(type);
                return;
            }
            throw new Exception(type.FullName);
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