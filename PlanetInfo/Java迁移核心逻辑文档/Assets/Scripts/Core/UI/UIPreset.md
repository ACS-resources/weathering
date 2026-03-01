# UIPreset.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/UI/UIPreset.cs`
- 命名空间：`Weathering`
- 代码行数：`141`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `class UIPresetResourceInsufficient`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class UIPresetInventoryFull`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class UIPresetInventoryFullTitle`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class InsufficientResource`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class InsufficientResourceTitle`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class UIPreset`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `public Notify(Action back, string content, string title = null)`
- `public ResourceInsufficient(Type type, Action back, long required, IInventory inventory)`
- `public ResourceInsufficientWithTag(Type type, Action back, long required, IInventory inventory)`
- `public InventoryFull(Action back, IInventory inventory, string extraContent = null)`
- `public OnTapItem(Action back, Type type)`
- `public Throw(string s)`

### 3.2 属性签名

- `public UIPresetResourceInsufficient`
- `public UIPresetInventoryFull`
- `public UIPresetInventoryFullTitle`
- `public InsufficientResource`
- `public InsufficientResourceTitle`
- `public UIPreset`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;

namespace Weathering
{
    [Concept]
    public class UIPresetResourceInsufficient { }

    [Concept]
    public class UIPresetInventoryFull { }
    [Concept]
    public class UIPresetInventoryFullTitle { }

    [Concept]
    public class InsufficientResource { }

    [Concept]
    public class InsufficientResourceTitle { }

    public static class UIPreset
    {
        //public static void ShowInventory(Action back, IInventory inventory) {
        //    List<IUIItem> items = new List<IUIItem>();
        //    if (back != null) {
        //        items.Add(UIItem.CreateReturnButton(back));
        //    }
        //    UIItem.AddEntireInventory(inventory, items, () => ShowInventory(back, inventory));
        //    UI.Ins.ShowItems("【背包】", items);
        //}

        public static void Notify(Action back, string content, string title = null) {
            UI.Ins.ShowItems(title == null ? "提示" : title
                , UIItem.CreateMultilineText(content)
                , UIItem.CreateReturnButton(back)
            );
        }

        public static void ResourceInsufficient<T>(Action back, long required, IValue value) {
            Type type = typeof(T);
            UI.Ins.ShowItems(Localization.Ins.Get<InsufficientResourceTitle>(),
                UIItem.CreateText(string.Format(Localization.Ins.Get<InsufficientResource>(), Localization.Ins.Val<T>(required))),
                UIItem.CreateValueProgress<T>(value),
                UIItem.CreateReturnButton(back)
            );
        }
        public static void ResourceInsufficient<T>(Action back, long required, IInventory inventory) {
            ResourceInsufficient(typeof(T), back, required, inventory);
        }
        public static void ResourceInsufficient(Type type, Action back, long required, IInventory inventory) {
            var items = new List<IUIItem>() {
                UIItem.CreateText(string.Format(Localization.Ins.Get<InsufficientResource>(), Localization.Ins.Val(type, required))),
                UIItem.CreateReturnButton(back),
            };

            if (inventory.CanRemove(type) > 0) {
                items.Add(UIItem.CreateSeparator());
                items.Add(UIItem.CreateInventoryItem(type, inventory, back, false));
            } else {
                items.Add(UIItem.CreateText("背包里没有相关资源"));
            }

            UI.Ins.ShowItems(Localization.Ins.Get<InsufficientResourceTitle>(), items);

            //UI.Ins.ShowItems(Localization.Ins.Get<InsufficientResourceTitle>(),
            //    UIItem.CreateText(string.Format(Localization.Ins.Get<InsufficientResource>(), Localization.Ins.Val(type, required))),
            //    UIItem.CreateReturnButton(back),

            //    UIItem.CreateSeparator(),
            //    UIItem.CreateInventoryTitle(),
            //    UIItem.CreateInventoryItem(type, inventory, back)
            //);
        }

        public static void ResourceInsufficientWithTag<T>(Action back, long required, IInventory inventory) {
            ResourceInsufficientWithTag(typeof(T), back, required, inventory);
        }
        public static void ResourceInsufficientWithTag(Type type, Action back, long required, IInventory inventory) {
            var items = new List<IUIItem>() {
                UIItem.CreateText(string.Format(Localization.Ins.Get<InsufficientResource>(), string.Format(Localization.Ins.Get(type), required))),
                UIItem.CreateReturnButton(back),
            };

            bool found = false;
            if (!inventory.Empty) {
                items.Add(UIItem.CreateSeparator());
                items.Add(UIItem.CreateText("【地图资源】中的相关资源"));

                foreach (var pair in inventory) {
                    if (Tag.HasTag(pair.Key, type)) {
                        found = true;
                        items.Add(UIItem.CreateInventoryItem(pair.Key, inventory, () => {
                            ResourceInsufficient(type, back, required, inventory);
                        }, false));
                    }
                }
            }
            if (!found) {
                items.Add(UIItem.CreateText("【地图资源】中, 没有任何相关资源"));
            }

            UI.Ins.ShowItems(Localization.Ins.Get<InsufficientResourceTitle>(), items);
        }


        public static void InventoryFull(Action back, IInventory inventory, string extraContent = null) {
            var items = new List<IUIItem>() {
            };

            items.Add(UIItem.CreateText(Localization.Ins.Get<UIPresetInventoryFull>()));

            if (extraContent != null) {
                items.Add(UIItem.CreateMultilineText(extraContent));
            }

            UIItem.AddEntireInventory(inventory, items, () => InventoryFull(back, inventory), false);
            UI.Ins.ShowItems(Localization.Ins.Get<UIPresetInventoryFullTitle>(), items);
        }

        public static void OnTapItem(Action back, Type type) {
            var items = UI.Ins.GetItems();

            if (back != null) items.Add(UIItem.CreateReturnButton(back));

            UIItem.AddItemDescription(items, type);

            UI.Ins.ShowItems(Localization.Ins.ValUnit(type), items);
        }

        public static void Throw(string s) {
            var items = UI.Ins.GetItems();

            items.Add(UIItem.CreateMultilineText(s));

            UI.Ins.ShowItems("程序发生错误! ! ! ", items);
            throw new Exception(s);
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