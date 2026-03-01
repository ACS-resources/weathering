# Concepts.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/Concept/Concepts.cs`
- 命名空间：`Weathering`
- 代码行数：`69`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `class Sanity`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Satiety`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class CoolDown`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class StateOfBuilding`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class StateOfIdle`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class StateOfProducing`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class StateOfAutomated`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class OperationUnavailable`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class PlayerAction`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Destruct`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Construct`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class ReturnMenu`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Management`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Harvest`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Sow`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Gather`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Terraform`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Deforestation`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Gathered`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class ProductionProgress`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Level`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Stage`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.2 属性签名

- `public Sanity`
- `public Satiety`
- `public CoolDown`
- `public StateOfBuilding`
- `public StateOfIdle`
- `public StateOfProducing`
- `public StateOfAutomated`
- `public OperationUnavailable`
- `public PlayerAction`
- `public Destruct`
- `public Construct`
- `public ReturnMenu`
- `public Management`
- `public Harvest`
- `public Sow`
- `public Gather`
- `public Terraform`
- `public Deforestation`
- `public Gathered`
- `public ProductionProgress`
- `public Level`
- `public Stage`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;

namespace Weathering
{

    [Concept]
    public class Sanity { }
    [Concept]
    public class Satiety { }
    [Concept]
    public class CoolDown { }


    [Concept]
    public class StateOfBuilding { }
    [Concept]
    public class StateOfIdle { }
    [Concept]
    public class StateOfProducing { }
    [Concept]
    public class StateOfAutomated { }


    [Concept]
    public class OperationUnavailable { }

    [Concept]
    public class PlayerAction { }
    [Concept]
    public class Destruct { }
    [Concept]
    public class Construct { }
    [Concept]
    public class ReturnMenu { }
    [Concept]
    public class Management { }
    [Concept]
    public class Harvest { }
    [Concept]
    public class Sow { }
    [Concept]
    public class Gather { }
    [Concept]
    public class Terraform { }

    [Concept]
    public class Deforestation { }

    [Concept]
    public class Gathered { }






    [Concept]
    public class ProductionProgress { }
    [Concept]
    public class Level { }
    [Concept]
    public class Stage { }


}

```

## 5. Java 迁移建议（本文件）

1. 先保留领域模型（类/接口）结构，再替换底层平台调用。
2. 若含 Unity API（如 `MonoBehaviour`、`Vector2Int`、`Tile`），先在 Java 中定义适配层接口与数据类。
3. 对外部可序列化字段保持字段语义与默认值一致，避免存档语义漂移。
4. 对反射型逻辑优先替换为“注册表 + 稳定 content_id”机制。
5. 将该文件纳入跨语言黄金样例测试，确保行为可回归。