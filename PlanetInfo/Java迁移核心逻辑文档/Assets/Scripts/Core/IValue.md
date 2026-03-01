# IValue.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/IValue.cs`
- 命名空间：`Weathering`
- 代码行数：`193`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `interface IValue`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class ValueData`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Value`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `public ToData(IValue value)`
- `public FromData(ValueData data)`
- `public Create(long val, long max, long inc, long dec, long del, long time)`
- `private Synchronize()`

### 3.2 属性签名

- `public IValue`
- `public ValueData`
- `public Time`
- `public Max`
- `public Del`
- `public Inc`
- `public Dec`
- `public Sur`
- `public Val`
- `public ProgressedTicks`
- `public RemainingTimeString`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;

namespace Weathering
{
    public interface IValue
    {
        long Val { get; set; } // 序列化
        long Max { get; set; } // 序列化
        long Inc { get; set; } // 序列化
        long Dec { get; set; }
        long Del { get; set; } // 序列化

        long Sur { get; }

        long Time { get; set; }
        bool Maxed { get; }
        // bool IsMaxed();

        string RemainingTimeString { get; }
        long ProgressedTicks { get; }
    }


    // class for serialization, struct for memory allocation
    public class ValueData
    {
        public long time = 0;
        public long inc = 0;
        public long dec = 0;
        public long del = 0;
        public long val = 0;
        public long max = 0;
    }

    public class Value : IValue
    {
        private Value() { }

        public static ValueData ToData(IValue value) {
            Value v = value as Value;
            if (v == null) throw new Exception();
            return new ValueData {
                time = v.time,
                inc = v.inc,
                dec = v.dec,
                del = v.del,
                val = v.val,
                max = v.max,
            };
        }
        public static IValue FromData(ValueData data) {
            return Create(data.val, data.max, data.inc, data.dec, data.del, data.time);
        }

        public const long MiniSecond = 10000;
        public const long Second = 1000 * MiniSecond;
        public const long Minute = 60 * Second;
        public const long Hour = 60 * Minute;
        public const long Day = 24 * Hour;

        private long time = 0;
        private long val = 0;
        private long inc = 0; // val difference
        private long dec = 0; // val difference
        private long del = Value.Second; // time diffence
        private long max = 0; // val limit


        public static Value Create(long val, long max, long inc, long dec, long del, long time) {
            return new Value {
                time = time,
                val = val,
                inc = inc,
                dec = dec,
                del = del,
                max = max
            };
        }

        private void Synchronize() {
            if (del == 0) return;
            long now = TimeUtility.GetTicks();
            long times = (now - time) / del;
            long newVal = val + times * (inc - dec);
            val = newVal > max ? max : newVal;
            time += times * del;
        }

        public long Time { get => time; set => time = value; }

        public long Max {
            get => max;
            set {
                Synchronize();
                if (Maxed) {
                    time = TimeUtility.GetTicks();
                }
                max = value;
            }
        }
        public long Del {
            get => del;
            set {
                Synchronize();
                time = TimeUtility.GetTicks();
                del = value;
            }
        }

        public long Inc {
            get => inc;
            set {
                Synchronize();
                inc = value;
                if (inc == 0) {
                    time = TimeUtility.GetTicks();
                }
            }
        }

        public long Dec {
            get => dec;
            set {
                Synchronize();
                dec = value;
            }
        }

        public long Sur {
            get => inc - dec;
        }

        public long Val {
            get {
                long now = TimeUtility.GetTicks();
                long times = del == 0 ? 0 : (now - time) / del;
                long newVal = val + times * Sur;
                return newVal > max ? max : newVal;
            }
            set {
                Synchronize();
                if (Maxed) {
                    time = TimeUtility.GetTicks();
                }
                val = value;
            }
        }

        public long ProgressedTicks {
            get {
                long now = TimeUtility.GetTicks();
                long progressedTicks = del == 0 || Sur == 0 ? 0 : (now - time) % del;
                return progressedTicks;
            }
        }

        public string RemainingTimeString {
            get {
                if (del == 0 || Sur == 0) return "生产停止";
                long remainingTicks = del - ProgressedTicks;

                const long ms2tick = 10000;
                const long s2ms = 1000;
                const long min2s = 60;
                const long h2min = 60;

                long miniSeconds = remainingTicks / ms2tick;
                long seconds = miniSeconds / s2ms;
                long minutes = seconds / min2s;
                long hours = minutes / h2min;

                if (hours > 0) {
                    return $"{hours} 时 {minutes - hours * h2min} 分";
                } else if (minutes > 0) {
                    return $"{minutes} 分 {seconds - minutes * min2s} 秒";
                } else if (seconds > 0) {
                    return $"{seconds} 秒 ";
                } else if (miniSeconds > 0) {
                    return $"{miniSeconds} 毫秒";
                }

                return "< 1ms";
            }
        }

        public bool Maxed => Val >= Max;
        // public bool IsMaxed() => Maxed;
    }
}

```

## 5. Java 迁移建议（本文件）

1. 先保留领域模型（类/接口）结构，再替换底层平台调用。
2. 若含 Unity API（如 `MonoBehaviour`、`Vector2Int`、`Tile`），先在 Java 中定义适配层接口与数据类。
3. 对外部可序列化字段保持字段语义与默认值一致，避免存档语义漂移。
4. 对反射型逻辑优先替换为“注册表 + 稳定 content_id”机制。
5. 将该文件纳入跨语言黄金样例测试，确保行为可回归。