# ConstructionCostBaseAttribute.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/Concept/ConstructionCostBaseAttribute.cs`
- 命名空间：`Weathering`
- 代码行数：`104`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `struct CostInfo`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class ConstructionCostBaseAttribute`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `public GetCost(Type type, IMap map, bool forConstruction)`
- `public GetCostMultiplier(Type type, IMap map, bool forConstruction, long countForDoubleCost)`
- `public ShowBuildingCostPage(Action back, IMap map, Type type)`

### 3.2 属性签名

- `public CostInfo`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp


using System;

namespace Weathering
{
    public struct CostInfo
    {
        public Type CostType;
        public long BaseCostQuantity;
        public long RealCostQuantity;
        public long CostMultiplier;
        public long CountForDoubleCost;
    }

    [AttributeUsage(AttributeTargets.Class)]
    public class ConstructionCostBaseAttribute : Attribute
    {
        public readonly Type CostType;
        public readonly long CostQuantity;
        public readonly long CountForDoubleCost;
        public ConstructionCostBaseAttribute(Type costType, long costQuantity, long costForDoubleCost = 10) {
            if (costType == null) throw new Exception(ToString());
            if (costQuantity < 0) throw new Exception(ToString());
            if (costQuantity == 0 && costForDoubleCost != 0) throw new Exception(ToString());
            if (costForDoubleCost < 0 || CountForDoubleCost >= 10000) throw new Exception(ToString());
            CostType = costType;
            CostQuantity = costQuantity;
            CountForDoubleCost = costForDoubleCost;
        }
        public static ValueTuple<Type, long> GetCostBase(Type type) {
            ConstructionCostBaseAttribute attr = Tag.GetAttribute<ConstructionCostBaseAttribute>(type);
            if (attr == null) {
                return (null, 0);
            }
            return (attr.CostType, attr.CostQuantity);
        }
        public static CostInfo GetCost(Type type, IMap map, bool forConstruction) {
            CostInfo result = new CostInfo();
            ConstructionCostBaseAttribute attr = Tag.GetAttribute<ConstructionCostBaseAttribute>(type);
            if (attr == null) {
                return result;
            }
            result.CostType = attr.CostType;
            result.BaseCostQuantity = attr.CostQuantity;
            result.CostMultiplier = GetCostMultiplier(type, map, forConstruction, attr.CountForDoubleCost);
            result.RealCostQuantity = attr.CostQuantity * result.CostMultiplier;
            result.CountForDoubleCost = attr.CountForDoubleCost;
            return result;
        }
        public static long GetCostMultiplier(Type type, IMap map, bool forConstruction, long countForDoubleCost) {
            long count = map.Refs.GetOrCreate(type).Value; // Map.Ref.Get<建筑>.Value, 为建筑数量。Map.Ref.Get<资源>.Value, 为资源产量
            if (!forConstruction) {
                // 计算拆除返还费用, 与建筑费用有1count的差距。如count为10时, 建筑费用增加, 拆除费用不变
                count--;
            }
            if (count < 0) throw new Exception($"建筑数量为负 {type.Name} {count}");

            //// 10个以上建筑时, 才开始增加费用
            //count = Math.Max(count - 10, 0);

            const long maximun = long.MaxValue / 100000;

            long multiplier = 1;

            if (countForDoubleCost != 0) {
                long magic = countForDoubleCost;
                long magic10 = magic * 10;

                while (count / magic10 > 0) {
                    count -= magic10;
                    multiplier *= 1000;

                    if (multiplier > maximun) break;
                }
                while (count / magic > 0) {
                    count -= magic;
                    multiplier *= 2;

                    if (multiplier > maximun) break;
                }
            }

            return multiplier;
        }


        public static void ShowBuildingCostPage(Action back, IMap map, Type type) {
            var items = UI.Ins.GetItems();

            if (back != null) items.Add(UIItem.CreateReturnButton(back));

            CostInfo cost = ConstructionCostBaseAttribute.GetCost(type, map, true);
            if (cost.CostType != null) {
                items.Add(UIItem.CreateText($"当前建筑费用: {Localization.Ins.Val(cost.CostType, cost.RealCostQuantity)}"));
                items.Add(UIItem.CreateText($"建筑费用乘数: {cost.CostMultiplier}"));
                items.Add(UIItem.CreateText($"费用增长系数: {cost.CountForDoubleCost}"));
            }
            items.Add(UIItem.CreateText($"同类建筑数量: {map.Refs.Get(type).Value}"));

            UI.Ins.ShowItems($"{Localization.Ins.Get(type)}建筑费用", items);
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