# GameConfig.cs（Java 迁移解构文档）

- 源文件：`Assets/GameEntry/GameConfig.cs`
- 命名空间：`Weathering`
- 代码行数：`95`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `class GameConfig`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class TutorialMapTheBook`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class TutorialMapTheDiary`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class TutorialMapTheCurse`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `public OnConstruct(IGlobals globals)`
- `public OnGameConstruct()`
- `public OnGameEnable()`
- `public OnSave()`

### 3.2 属性签名

- `public GameConfig`
- `public DefaultInventoryOfResourceQuantityCapacity`
- `public DefaultInventoryOfResourceTypeCapacity`
- `public DefaultInventoryOfSupplyQuantityCapacity`
- `public DefaultInventoryOfSupplyTypeCapacity`
- `public TutorialMapTheBook`
- `public TutorialMapTheDiary`
- `public TutorialMapTheCurse`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp


using System.Collections.Generic;
using UnityEngine;

namespace Weathering
{
	/// <summary>
	/// 发布时和测试时, 需要改哪几个地方? 
	/// GlobalGameEvents的设置
	/// </summary>
	public static class GameConfig
	{
		public static bool CheatMode = false;
		public static long DefaultInventoryOfResourceQuantityCapacity { get; } = 1000000000000000;
		public static int DefaultInventoryOfResourceTypeCapacity { get; } = 30;
		public static long DefaultInventoryOfSupplyQuantityCapacity { get; } = 10000000000;
		public static int DefaultInventoryOfSupplyTypeCapacity { get; } = 10;

		public const string InitialMapKey = "Weathering.MapOfPlanet#=1,4=14,93=24,31";

		public const int VersionCode = 20210417;
		public static void OnConstruct(IGlobals globals) {

			// 全局理智
			IValue sanity = globals.Values.Create<Sanity>();
			sanity.Max = 100;
			sanity.Val = sanity.Max / 10;
			sanity.Inc = 1;
			sanity.Del = 10 * Value.Second;

			// 饱腹度
			IValue satiety = globals.Values.Create<Satiety>();
			satiety.Max = 100;
			satiety.Inc = 1;
			satiety.Val = 0;
			satiety.Del = Value.Second;

			// 行动冷却
			IValue cooldown = globals.Values.Create<CoolDown>();
			cooldown.Inc = 1;
			cooldown.Max = 1;
			cooldown.Del = Value.Second;

			IInventory inventory = globals.Inventory;
			inventory.QuantityCapacity = DefaultInventoryOfResourceQuantityCapacity;
			inventory.TypeCapacity = 10;

			inventory.Add<TutorialMapTheBook>(1);
			inventory.Add<TutorialMapTheDiary>(1);
			inventory.Add<TutorialMapTheCurse>(1);


			Globals.Ins.Values.GetOrCreate<QuestResource>().Del = Value.Second;

			Globals.Unlock<TotemOfNature>();

			Globals.Ins.Values.GetOrCreate<KnowledgeOfNature>().Max = KnowledgeOfNature.Max;
			Globals.Ins.Values.GetOrCreate<KnowledgeOfAncestors>().Max = KnowledgeOfAncestors.Max;

			if (!CheatMode) {
				SpecialPages.OpenStartingPage();
			}

		}

		public static void OnGameConstruct() {

		}

		public static void OnGameEnable() {

		}

		public static void OnSave() {

		}


	}





	[Depend(typeof(Book))]
	public class TutorialMapTheBook { }

	[Depend(typeof(Book))]
	public class TutorialMapTheDiary { }

	[Depend(typeof(Book))]
	public class TutorialMapTheCurse { }
}

```

## 5. Java 迁移建议（本文件）

1. 先保留领域模型（类/接口）结构，再替换底层平台调用。
2. 若含 Unity API（如 `MonoBehaviour`、`Vector2Int`、`Tile`），先在 Java 中定义适配层接口与数据类。
3. 对外部可序列化字段保持字段语义与默认值一致，避免存档语义漂移。
4. 对反射型逻辑优先替换为“注册表 + 稳定 content_id”机制。
5. 将该文件纳入跨语言黄金样例测试，确保行为可回归。