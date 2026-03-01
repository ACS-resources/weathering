# MainQuest.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/MainQuest/MainQuest.cs`
- 命名空间：`Weathering`
- 代码行数：`187`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `class QuestResource`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class QuestRequirement`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class CurrentQuest`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class MainQuest`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `private Awake()`

### 3.2 属性签名

- `public QuestResource`
- `public QuestRequirement`
- `public CurrentQuest`
- `public Ins`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;

namespace Weathering
{
    public class QuestResource { }
    public class QuestRequirement { }
    public class CurrentQuest { }

    public class MainQuest : MonoBehaviour
    {
        public static MainQuest Ins { get; private set; }
        private void Awake() {
            if (Ins != null) throw new Exception();
            Ins = this;
        }

        //private AudioClip questCompleteSound;
        //// private AudioClip questCanBeCompletedSound;
        //private IRef currentQuest;
        //public Type CurrentQuest {
        //    get => currentQuest.Type;
        //    private set => currentQuest.Type = value;
        //}

        //private void Start() {
        //    questCompleteSound = Sound.Ins.Get("mixkit-magic-potion-music-and-fx-2831");
        //    // questCanBeCompletedSound = Sound.Ins.Get("mixkit-positive-notification-951");
        //    currentQuest = Globals.Ins.Refs.GetOrCreate<CurrentQuest>();
        //    if (CurrentQuest == null) {
        //        Type startingQuest = MainQuestConfig.StartingQuest;
        //        MainQuestConfig.Ins.OnStartQuest.TryGetValue(startingQuest, out Action action);
        //        action?.Invoke();
        //        CurrentQuest = startingQuest;
        //        currentQuest.Value = MainQuestConfig.Ins.GetIndex(startingQuest); // x for index

        //        //// 自动做完所有初始任务的前置任务。第一次游戏/开发时生效
        //        //foreach (var quest in MainQuestConfig.Ins.QuestSequence) {
        //        //    Globals.Ins.Bool(quest, true);
        //        //    if (quest == startingQuest) break;
        //        //}
        //    }
        //}

        //public bool IsUnlocked<T>() => MainQuestConfig.Ins.GetIndex(typeof(T)) <= MainQuestConfig.Ins.GetIndex(CurrentQuest);// return Globals.Ins.Bool<T>();
        //public bool IsOnOrBefore<T>() => MainQuestConfig.Ins.GetIndex(typeof(T)) >= MainQuestConfig.Ins.GetIndex(CurrentQuest);// return Globals.Ins.Bool<T>();

        //public void CompleteQuest<T>() => CompleteQuest(typeof(T));
        //public void CompleteQuest(Type type) {
        //    if (CurrentQuest != type) return;

        //    Sound.Ins.Play(questCompleteSound); // 任务完成音效
        //    Type oldQuest = CurrentQuest; // 刚完成的任务
        //    Type newQuest = MainQuestConfig.Ins.QuestSequence[(int)currentQuest.Value + 1]; // 新的任务
        //    string questNameOld = Localization.Ins.Get(oldQuest);
        //    string questNameNew = Localization.Ins.Get(newQuest);
        //    // Globals.Ins.Bool(newQuest, true); // 任何已完成或者正在进行的任务, 标记。已经不需要了
        //    currentQuest.Value++; // 主线任务下标
        //    CurrentQuest = newQuest; // 保存正在进行的主线任务

        //    Globals.Ins.Refs.GetOrCreate<QuestResource>().Type = null; // 需求任务消耗物品类型：无
        //    Globals.Ins.Values.GetOrCreate<QuestResource>().Max = 0; // 需求任务消耗物品数量：0
        //    Globals.Ins.Refs.GetOrCreate<QuestRequirement>().Type = null; // 需求任务用有物品：空
        //    MainQuestConfig.Ins.OnStartQuest.TryGetValue(newQuest, out Action action);
        //    action?.Invoke(); // 设置新任务需求任务物品

        //    var items = UI.Ins.GetItems();
        //    items.Add(UIItem.CreateBanner("questComplete")); // “任务完成”横幅
        //    items.Add(UIItem.CreateButton($"查看下一个任务 {questNameNew}", OnTap));

        //    items.Add(UIItem.CreateButton($"回顾刚完成任务 {questNameOld}", () => {
        //        var items_ = UI.Ins.GetItems();

        //        items.Add(UIItem.CreateButton("查看下一个任务", OnTap));

        //        MainQuestConfig.Ins.OnTapQuest[oldQuest](items_);
        //        UI.Ins.ShowItems("刚完成任务", items_);
        //    }));

        //    if (questNameOld == null) {
        //        questNameOld = $"【任务目标完成】";
        //    } else {
        //        questNameOld = $"【任务目标完成】{questNameOld}";
        //    }
        //    UI.Ins.ShowItems(questNameOld, items);
        //}

        //public void ViewAllQuests(Action back) {
        //    var items = UI.Ins.GetItems();
        //    foreach (Type quest in MainQuestConfig.Ins.QuestSequence) {
        //        items.Add(UIItem.CreateButton(Localization.Ins.Get(quest), () => {
        //            var items_ = UI.Ins.GetItems();
        //            items_.Add(UIItem.CreateReturnButton(() => ViewAllQuests(back)));

        //            // 任务介绍
        //            if (MainQuestConfig.Ins.OnTapQuest.TryGetValue(quest, out var onTapQuest)) {
        //                onTapQuest(items_);
        //            } else {
        //                // throw new Exception($"没有配置任务内容{currentQuest.Type}");
        //                MainQuestConfig.QuestConfigNotProvidedThrowException(quest);
        //            }

        //            UI.Ins.ShowItems(Localization.Ins.Get(quest), items_);
        //        }));
        //    }
        //    UI.Ins.ShowItems("所有任务的列表", items);
        //}

        //public void OnTap() {
        //    var items = UI.Ins.GetItems();

        //    IMap map = MapView.Ins.TheOnlyActiveMap;

        //    // 以提交物品方式做的任务
        //    IValue ValueOfResource = Globals.Ins.Values.GetOrCreate<QuestResource>();
        //    IRef TypeOfResource = Globals.Ins.Refs.GetOrCreate<QuestResource>();
        //    if (TypeOfResource.Type != null) {
        //        items.Add(UIItem.CreateDynamicButton("提交任务", () => {
        //            CompleteQuest(CurrentQuest);
        //        }, () => ValueOfResource.Maxed)); // 资源任务的提交条件：ValueOfResource.Maxed

        //        items.Add(UIItem.CreateDynamicButton($"提交任务物品{Localization.Ins.ValUnit(TypeOfResource.Type)}", () => {
        //            long quantity = Math.Min(ValueOfResource.Max - ValueOfResource.Val, map.Inventory.GetWithTag(TypeOfResource.Type));
        //            map.Inventory.RemoveWithTag(TypeOfResource.Type, quantity);
        //            ValueOfResource.Val += quantity;
        //            OnTap();
        //        }, () => !ValueOfResource.Maxed && map.Inventory.GetWithTag(TypeOfResource.Type) > 0));

        //        items.Add(UIItem.CreateValueProgress(TypeOfResource.Type, ValueOfResource));

        //        items.Add(UIItem.CreateText("已有【任务相关物品】如下"));
        //        long count = UIItem.AddEntireInventoryContentWithTag(TypeOfResource.Type, map.Inventory, items, OnTap, false);
        //        if (count == 0) {
        //            items.Add(UIItem.CreateText("没有任何【任务相关物品】"));
        //        }
        //    }

        //    // 以拥有物品方式做的任务
        //    IRef TypeOfRequirement = Globals.Ins.Refs.GetOrCreate<QuestRequirement>();
        //    IValue ValueOfRequirement = Globals.Ins.Values.GetOrCreate<QuestRequirement>();
        //    if (TypeOfRequirement.Type != null) {

        //        long quantity = map.Inventory.GetWithTag(TypeOfRequirement.Type);
        //        ValueOfRequirement.Val = quantity;

        //        items.Add(UIItem.CreateStaticButton("提交任务", () => {
        //            CompleteQuest(CurrentQuest);
        //        }, ValueOfRequirement.Maxed));

        //        items.Add(UIItem.CreateText("已有【任务相关物品】如下"));
        //        long count = UIItem.AddEntireInventoryContentWithTag(TypeOfRequirement.Type, map.Inventory, items, OnTap, false);
        //        if (count == 0) {
        //            items.Add(UIItem.CreateText("没有任何【任务相关物品】"));
        //        }
        //    }

        //    // 自定义条件任务
        //    if (MainQuestConfig.Ins.CanCompleteQuest.TryGetValue(CurrentQuest, out Func<bool> canCompleteQuest)) {
        //        items.Add(UIItem.CreateDynamicButton("提交任务", () => {
        //            CompleteQuest(CurrentQuest);
        //        }, canCompleteQuest));
        //    }

        //    items.Add(UIItem.CreateSeparator());

        //    // 任务介绍
        //    if (MainQuestConfig.Ins.OnTapQuest.TryGetValue(CurrentQuest, out var onTapQuest)) {
        //        onTapQuest(items);
        //    } else {
        //        // throw new Exception($"没有配置任务内容{currentQuest.Type}");
        //        MainQuestConfig.QuestConfigNotProvidedThrowException(CurrentQuest);
        //    }

        //    // 任务标题
        //    string title = Localization.Ins.Get(CurrentQuest);
        //    if (title == null) {
        //        title = $"【任务进行中】";
        //    } else {
        //        title = $"【任务进行中】{title}";
        //    }
        //    UI.Ins.ShowItems(title, items);
        //}
    }
}

```

## 5. Java 迁移建议（本文件）

1. 先保留领域模型（类/接口）结构，再替换底层平台调用。
2. 若含 Unity API（如 `MonoBehaviour`、`Vector2Int`、`Tile`），先在 Java 中定义适配层接口与数据类。
3. 对外部可序列化字段保持字段语义与默认值一致，避免存档语义漂移。
4. 对反射型逻辑优先替换为“注册表 + 稳定 content_id”机制。
5. 将该文件纳入跨语言黄金样例测试，确保行为可回归。