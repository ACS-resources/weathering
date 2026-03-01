# UIItem.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/UI/UIItem.cs`
- 命名空间：`Weathering`
- 代码行数：`651`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `enum IUIBackgroundType`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `enum IUIItemType`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `interface IUIItem`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class UIItemInventoryQuantityCapacity`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class UIItemInventoryTypeCapacity`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class UIItemDecIncMaxText`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class UIItem`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `private InitializeLocalizationText()`
- `public CreateSeparator()`
- `public CreateTransparency(int scale = 256)`
- `public CreateInventoryCapacity(IInventory inventory)`
- `public CreateInventoryTypeCapacity(IInventory inventory)`
- `private AddEntireInventoryHead(IInventory inventory, List<IUIItem> items)`
- `public AddEntireInventoryContent(IInventory inventory, List<IUIItem> items, Action back, bool canDiscard)`
- `public AddEntireInventory(IInventory inventory, List<IUIItem> items, Action back, bool canDiscard)`
- `public AddEntireInventoryContentWithTag(Type type, IInventory inventory, List<IUIItem> items, Action back, bool canDiscard)`
- `public CreateInventoryItem(Type type, IInventory inventory, Action back, bool canDiscard)`
- `private OnTapInventoryItem(IInventory inventory, Type type, Action back, bool canDiscard)`
- `public AddItemDescription(List<IUIItem> items, Type type)`
- `public CreateMultilineText(string text)`
- `public CreateFAQText(string faq, string text)`
- `public CreateText(string text)`
- `public CreateDynamicText(Func<string> dynamicText)`
- `public CreateValueProgress(Type type, IValues values)`
- `public CreateValueProgress(Type type, IValue value)`
- `public CreateTimeProgress(Type type, IValues values)`
- `public CreateTimeProgress(Type type, IValue value)`
- `public CreateBanner(string name)`
- `public CreateButton(string label, Action onTap)`
- `public CreateIconButton(string label, string icon, Action onTap)`
- `public CreateStaticButton(string label, Action onTap, bool interactable)`
- `public CreateDynamicButton(string label, Action onTap, Func<bool> canTap)`
- `public CreateDynamicIconButton(string label, Action onTap, Func<bool> canTap, string icon)`
- `public CreateDynamicContentButton(Func<string> label, Action onTap, Func<bool> canTap = null)`
- `public CreateReturnButton(Action back)`
- `public CreateStaticDestructButton(ITile tile, Action back = null)`
- `private CreateComplexConstructionButton(Type type, ITile tile)`
- `public CreateConstructionButton(Type type, ITile tile)`
- `public CreateTileImage(Type tileType)`
- `public CreateTileImage(string tileType, int scale = 4)`
- `public CreateRawImage(string tileType, int scale = 2)`

### 3.2 属性签名

- `public IUIBackgroundType`
- `public IUIItemType`
- `public IUIItem`
- `public UIItemInventoryQuantityCapacity`
- `public UIItemInventoryTypeCapacity`
- `public UIItemDecIncMaxText`
- `public Type`
- `public BackgroundType`
- `public Scale`
- `public LeftPadding`
- `public Interactable`
- `public Content`
- `public Icon`
- `public DynamicContent`
- `public Value`
- `public OnTap`
- `public CanTap`
- `public InitialSliderValue`
- `public HasShortcut`
- `public ShortcutMap`
- `public ShortcutType`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;

namespace Weathering
{

    public enum IUIBackgroundType
    {
        None, Transparent, Solid, SemiTranspanrent, Button, ButtonBack, InventoryItem
    }
    public enum IUIItemType
    {
        None, OnelineDynamicText, OnelineStaticText, MultilineText,
        Separator, Image, Transparency,
        Button, ValueProgress, TimeProgress, SurProgress, Slider
    }

    public interface IUIItem
    {
        IUIItemType Type { get; }
        IUIBackgroundType BackgroundType { get; }
        string Content { get; }
        string Icon { get; set; }
        int Scale { get; set; }
        int LeftPadding { get; set; }
        bool Interactable { get; set; }
        Func<string> DynamicContent { get; set; }
        Func<float, string> DynamicSliderContent { get; set; }
        IValue Value { get; set; }
        Action OnTap { get; set; }
        Func<bool> CanTap { get; set; }

        float InitialSliderValue { get; set; }
    }

    [Concept]
    public class UIItemInventoryQuantityCapacity { }

    [Concept]
    public class UIItemInventoryTypeCapacity { }

    [Concept]
    public class UIItemDecIncMaxText { }

    public class UIItem : IUIItem
    {


        public IUIItemType Type { get; set; } = IUIItemType.None;
        public IUIBackgroundType BackgroundType { get; set; } = IUIBackgroundType.SemiTranspanrent;
        public int Scale { get; set; } = 1;
        public int LeftPadding { get; set; } = 64;
        public bool Interactable { get; set; } = true;
        public string Content { get; set; }
        public string Icon { get; set; }
        public Func<string> DynamicContent { get; set; }
        public Func<float, string> DynamicSliderContent { get; set; }
        public IValue Value { get; set; }
        public Action OnTap { get; set; }
        public Func<bool> CanTap { get; set; }
        public float InitialSliderValue { get; set; }


        private static bool initialized = false;
        private static void InitializeLocalizationText() {
            if (initialized) return;
            initialized = true;

            uiitemInventoryQuantityCapacity = Localization.Ins.Get<UIItemInventoryQuantityCapacity>();
            uiitemInventoryTypeCapacity = Localization.Ins.Get<UIItemInventoryTypeCapacity>();
            uiitemDecIncMaxText = Localization.Ins.Get<UIItemDecIncMaxText>();
        }

        /// <summary>
        /// 横条分隔
        /// </summary>
        /// <returns></returns>
        public static UIItem CreateSeparator() {
            return new UIItem {
                Type = IUIItemType.Separator,
            };
        }

        /// <summary>
        /// 透明分割 (默认256像素高)
        /// </summary>
        public static UIItem CreateTransparency(int scale = 256) {
            return new UIItem {
                Type = IUIItemType.Transparency,
                Scale = scale,
            };
        }


        ///// <summary>
        ///// 背包两个字
        ///// </summary>
        //public static IUIItem CreateInventoryTitle() {
        //    return new UIItem() {
        //        Type = IUIItemType.OnelineStaticText,
        //        Content = Localization.Ins.Get<PlayerInventory>(),
        //    };
        //}

        /// <summary>
        /// 背包容量动态文本
        /// </summary>
        private static string uiitemInventoryQuantityCapacity;
        public static IUIItem CreateInventoryCapacity(IInventory inventory) {
            InitializeLocalizationText();
            return new UIItem() {
                Type = IUIItemType.OnelineDynamicText,
                DynamicContent = () => string.Format(uiitemInventoryQuantityCapacity, inventory.Quantity, inventory.QuantityCapacity),
            };
        }

        /// <summary>
        /// 背包类型容量动态文本
        /// </summary>
        private static string uiitemInventoryTypeCapacity;
        public static IUIItem CreateInventoryTypeCapacity(IInventory inventory) {
            InitializeLocalizationText();
            return new UIItem() {
                Type = IUIItemType.OnelineDynamicText,
                DynamicContent = () => string.Format(uiitemInventoryTypeCapacity, inventory.TypeCount, inventory.TypeCapacity),
            };
        }

        private static void AddEntireInventoryHead(IInventory inventory, List<IUIItem> items) {
            // items.Add(CreateInventoryTitle());
            items.Add(CreateInventoryCapacity(inventory));
            items.Add(CreateInventoryTypeCapacity(inventory));
        }

        /// <summary>
        /// 背包内容
        /// </summary>
        public static void AddEntireInventoryContent(IInventory inventory, List<IUIItem> items, Action back, bool canDiscard) {
            IInventoryDefinition definition = inventory as IInventoryDefinition;
            if (definition == null) throw new Exception();
            foreach (var pair in definition.Dict) {
                items.Add(CreateInventoryItem(pair.Key, inventory, back, canDiscard));
            }
        }

        /// <summary>
        /// 背包头和背包内容
        /// </summary>
        /// <param name="inventory"></param>
        /// <param name="items"></param>
        /// <param name="back"></param>
        public static void AddEntireInventory(IInventory inventory, List<IUIItem> items, Action back, bool canDiscard) {
            IInventoryDefinition definition = inventory as IInventoryDefinition;
            if (definition == null) throw new Exception();
            AddEntireInventoryHead(inventory, items);
            AddEntireInventoryContent(inventory, items, back, canDiscard);
        }


        public static long AddEntireInventoryContentWithTag<T>(IInventory inventory, List<IUIItem> items, Action back, bool canDiscard) {
            return AddEntireInventoryContentWithTag(typeof(T), inventory, items, back, canDiscard);
        }

        public static long AddEntireInventoryContentWithTag(Type type, IInventory inventory, List<IUIItem> items, Action back, bool canDiscard) {
            IInventoryDefinition definition = inventory as IInventoryDefinition;
            if (definition == null) throw new Exception();
            long count = 0;
            foreach (var pair in definition.Dict) {
                if (Tag.HasTag(pair.Key, type)) {
                    items.Add(CreateInventoryItem(pair.Key, inventory, back, canDiscard));
                    count++;
                }
            }
            return count;
        }

        public static void AddEntireInventoryWithTag<T>(IInventory inventory, List<IUIItem> items, Action back, bool canDiscard) {
            IInventoryDefinition definition = inventory as IInventoryDefinition;
            if (definition == null) throw new Exception();
            AddEntireInventoryHead(inventory, items);
            AddEntireInventoryContentWithTag<T>(inventory, items, back, canDiscard);
        }

        private static float UseItem_SliderValue = 0;
        private static long UseItem_SliderValueRounded = 0;
        private static float DiscardItem_SliderValue = 0;
        private static long DiscardItem_SliderValueRounded = 0;

        /// <summary>
        /// 一项内容
        /// </summary>
        public static UIItem CreateInventoryItem<T>(IInventory inventory, Action back, bool canDiscard) {
            return CreateInventoryItem(typeof(T), inventory, back, canDiscard);
        }
        public static UIItem CreateInventoryItem(Type type, IInventory inventory, Action back, bool canDiscard) {
            return new UIItem() {
                Type = IUIItemType.Button,
                BackgroundType = IUIBackgroundType.InventoryItem,
                Icon = type.Name,
                Content = $"{Localization.Ins.Val(type, inventory.CanRemove(type))}",
                OnTap = () => {
                    OnTapInventoryItem(inventory, type, back, canDiscard);
                }
            };
        }

        /// <summary>
        /// 背包项目被按时, 会发生什么? 在这里写了
        /// </summary>
        private static void OnTapInventoryItem(IInventory inventory, Type type, Action back, bool canDiscard) {
            if (back == null) throw new Exception();

            var items = UI.Ins.GetItems();

            // 返回按钮
            items.Add(CreateReturnButton(back));

            long quantity = inventory.CanRemove(type);
            // 此内容数量
            items.Add(new UIItem {
                Type = IUIItemType.OnelineDynamicText,
                DynamicContent = () => $"数量 {quantity}"
            });

            if (ItemUsage.Usage.TryGetValue(type, out var action)) {
                items.Add(new UIItem {
                    Type = IUIItemType.Slider,
                    InitialSliderValue = 1,
                    DynamicSliderContent = (float x) => {
                        UseItem_SliderValue = x;
                        UseItem_SliderValueRounded = (long)Mathf.Round(UseItem_SliderValue * inventory.CanRemove(type));
                        return $"选择使用数量 {UseItem_SliderValueRounded}";
                    }
                });
                items.Add(CreateButton("确认使用物品", () => action.Invoke(inventory, UseItem_SliderValueRounded, () => { OnTapInventoryItem(inventory, type, back, canDiscard); })));
                items.Add(CreateSeparator());
            }

            AddItemDescription(items, type);

            if (canDiscard && Tag.HasTag(type, typeof(Discardable))) {
                items.Add(new UIItem {
                    Type = IUIItemType.Slider,
                    DynamicSliderContent = (float x) => {
                        DiscardItem_SliderValue = x;
                        DiscardItem_SliderValueRounded = (long)Mathf.Round(DiscardItem_SliderValue * inventory.CanRemove(type));
                        return $"选择丢弃数量 {DiscardItem_SliderValueRounded}";
                    }
                });
                items.Add(new UIItem {
                    Type = IUIItemType.Button,
                    DynamicContent = () => $"确认丢弃 {DiscardItem_SliderValueRounded}",
                    OnTap = () => {
                        if (DiscardItem_SliderValueRounded == inventory.CanRemove(type)) {
                            UI.Ins.Active = false;
                        }
                        inventory.Remove(type, DiscardItem_SliderValueRounded);
                        back?.Invoke();
                    },
                });
                items.Add(CreateSeparator());
            }

            UI.Ins.ShowItems(Localization.Ins.ValUnit(type), items);

        }
        public static void AddItemDescription(List<IUIItem> items, Type type) {

            // 资源特性
            List<Type> allTags = Tag.AllTagOf(type);
            if (allTags != null && allTags.Count > 0) {
                System.Text.StringBuilder sb = new System.Text.StringBuilder();
                sb.Append("资源特性：");
                foreach (var tag in allTags) {
                    if (Tag.HasTag(type, typeof(InventoryItemResource))) {
                        sb.Append(Localization.Ins.ValUnit(tag));
                    } else {
                        sb.Append(Localization.Ins.Get(tag));
                    }
                }
                items.Add(CreateMultilineText(sb.ToString()));
                items.Add(CreateSeparator());
            }


            // 子类物品
            List<Type> allsubtag = Tag.AllSubTagOf(type);
            if (allsubtag != null && allsubtag.Count > 0) {
                System.Text.StringBuilder sb = new System.Text.StringBuilder();
                sb.Append("子类资源：");
                foreach (var tag in allsubtag) {
                    if (Tag.HasTag(type, typeof(InventoryItemResource))) {
                        sb.Append(Localization.Ins.ValUnit(tag));
                    } else {
                        sb.Append(Localization.Ins.Get(tag));
                    }
                }
                items.Add(CreateMultilineText(sb.ToString()));
                items.Add(CreateSeparator());
            }

            string description = Localization.Ins.GetDescription(type);
            if (description != null) {
                items.Add(CreateMultilineText(description));
                // 物品图片
            }
            items.Add(CreateTileImage(type));

            //// 物品描述
            //var inventoryItemDescription = Attribute.GetCustomAttribute(type, typeof(ConceptDescription)) as ConceptDescription;
            //if (inventoryItemDescription != null) {
            //    items.Add(CreateMultilineText(Localization.Ins.Get(inventoryItemDescription.DescriptionKey)));
            //    // 物品图片
            //    items.Add(CreateTileImage(type));
            //} else {
            //    // items.Add(CreateText("【此资源描述文案有待完善】"));
            //}
        }

        /// <summary>
        /// 多行文本
        /// </summary>
        public static UIItem CreateMultilineText(string text) {
            return new UIItem() {
                Type = IUIItemType.MultilineText,
                Content = text,
            };
        }
        public static UIItem CreateFAQText(string faq, string text) {
            return CreateMultilineText($"\n<color=#ff9999>({faq}) </color>\n{text}");
        }

        /// <summary>
        /// 单行文本
        /// </summary>
        public static UIItem CreateText(string text) {
            return new UIItem() {
                Type = IUIItemType.OnelineStaticText,
                Content = text,
            };
        }

        /// <summary>
        /// 动态单行文本
        /// </summary>
        public static UIItem CreateDynamicText(Func<string> dynamicText) {
            return new UIItem() {
                Type = IUIItemType.OnelineDynamicText,
                DynamicContent = dynamicText,
            };
        }

        /// <summary>
        /// 已弃用
        /// </summary>
        private static string uiitemDecIncMaxText;
        public static UIItem CreateDecIncMaxText<T>(IValue value) {
            InitializeLocalizationText();
            return new UIItem() {
                Type = IUIItemType.OnelineDynamicText,
                DynamicContent = () => $"{Localization.Ins.ValUnit<T>()}{string.Format(uiitemDecIncMaxText, value.Dec, value.Inc, value.Max)}"
            };
        }


        /// <summary>
        /// val max 进度条
        /// </summary>
        public static UIItem CreateValueProgress<T>(IValues values) {
            return CreateValueProgress(typeof(T), values);
        }
        public static UIItem CreateValueProgress(Type type, IValues values) {
            return new UIItem() {
                Content = Localization.Ins.ValUnit(type),
                Type = IUIItemType.ValueProgress,
                Value = values.Get(type)
            };
        }
        public static UIItem CreateValueProgress<T>(IValue value) {
            return CreateValueProgress(typeof(T), value);
        }
        public static UIItem CreateValueProgress(Type type, IValue value) {
            return new UIItem() {
                Content = Localization.Ins.ValUnit(type),
                Type = IUIItemType.ValueProgress,
                Value = value
            };
        }

        /// <summary>
        /// time del 进度条
        /// </summary>
        public static UIItem CreateTimeProgress<T>(IValues values) {
            return CreateTimeProgress(typeof(T), values);
        }
        public static UIItem CreateTimeProgress(Type type, IValues values) {
            return new UIItem() {
                Content = Localization.Ins.ValUnit(type),
                Type = IUIItemType.TimeProgress,
                Value = values.Get(type)
            };
        }

        public static UIItem CreateTimeProgress<T>(IValue value) {
            return new UIItem() {
                Content = Localization.Ins.ValUnit<T>(),
                Type = IUIItemType.TimeProgress,
                Value = value
            };
        }
        public static UIItem CreateTimeProgress(Type type, IValue value) {
            return new UIItem() {
                Content = Localization.Ins.ValUnit(type),
                Type = IUIItemType.TimeProgress,
                Value = value
            };
        }

        /// <summary>
        /// dec inc sur 进度条
        /// </summary>
        public static UIItem CreateSurProgress<T>(IValues values) {
            return new UIItem() {
                Content = Localization.Ins.ValUnit<T>(),
                Type = IUIItemType.SurProgress,
                Value = values.Get<T>()
            };
        }
        public static UIItem CreateSurProgress<T>(IValue value) {
            return new UIItem() {
                Content = Localization.Ins.ValUnit<T>(),
                Type = IUIItemType.SurProgress,
                Value = value
            };
        }

        //public static UIItem ShowInventoryButton(Action back, IInventory inventory) {
        //    return CreateButton("查看背包", () => {
        //        UIPreset.ShowInventory(back, inventory);
        //    });
        //}

        public static UIItem CreateBanner(string name) {
            return new UIItem {
                Type = IUIItemType.Image,
                LeftPadding = 0,
                Content = name
            };
        }

        public static UIItem CreateButton(string label, Action onTap) {
            return new UIItem {
                Type = IUIItemType.Button,
                Content = label,
                OnTap = onTap,
                Interactable = true,
            };
        }

        public static UIItem CreateIconButton(string label, string icon, Action onTap) {
            return new UIItem {
                Type = IUIItemType.Button,
                Content = label,
                Icon = icon,
                OnTap = onTap,
                Interactable = true,
            };
        }

        public static UIItem CreateStaticButton(string label, Action onTap, bool interactable) {
            return new UIItem {
                Type = IUIItemType.Button,
                Content = label,
                OnTap = onTap,
                Interactable = interactable,
            };
        }

        public static UIItem CreateDynamicButton(string label, Action onTap, Func<bool> canTap) {
            return new UIItem {
                Type = IUIItemType.Button,
                Content = label,
                OnTap = onTap,
                CanTap = canTap,
            };
        }
        public static UIItem CreateDynamicIconButton(string label, Action onTap, Func<bool> canTap, string icon) {
            return new UIItem {
                Type = IUIItemType.Button,
                Content = label,
                OnTap = onTap,
                CanTap = canTap,
                Icon = icon,
            };
        }

        public static UIItem CreateDynamicContentButton(Func<string> label, Action onTap, Func<bool> canTap = null) {
            return new UIItem {
                Type = IUIItemType.Button,
                DynamicContent = label,
                OnTap = onTap,
                CanTap = canTap,
            };
        }

        public static UIItem CreateReturnButton(Action back) {
            UIItem result = null;
            string title = string.Empty; // Localization.Ins.Get<ReturnMenu>();
            if (back == null) result = CreateButton(title, () => UI.Ins.Active = false);
            else result = CreateButton(title, back);
            result.BackgroundType = IUIBackgroundType.ButtonBack;
            return result;
        }

        public static UIItem CreateDynamicDestructButton<T>(ITile tile, Func<bool> canTap = null, Action back = null) where T : class, ITile {
            return new UIItem {
                Type = IUIItemType.Button,
                Content = $"{Localization.Ins.Get<Destruct>()}",
                OnTap =
                    () => {
                        tile.GetMap().UpdateAt<T>(tile);
                        if (back == null) {
                            UI.Ins.Active = false;
                        } else {
                            back.Invoke();
                        }
                    }
                ,
                CanTap = canTap,
            };
        }
        public static UIItem CreateStaticDestructButton(ITile tile, Action back = null) {
            return new UIItem {
                Type = IUIItemType.Button,
                Content = $"{Localization.Ins.Get<Destruct>()}",
                OnTap =
                    () => {
                        IMap map = tile.GetMap();
                        map.UpdateAt(map.DefaultTileType, tile);
                        if (back == null) {
                            UI.Ins.Active = false;
                        } else {
                            back.Invoke();
                        }
                    }
                ,
                Interactable = tile.CanDestruct()
            };
        }

        public static bool HasShortcut { get; private set; }
        public static IMap ShortcutMap { get; private set; }

        private static Type shortcutType = null;
        public static Type ShortcutType {
            get => shortcutType; set {
                // 这里有个强耦合, 能产矿石的建筑类型, 无视快捷方式
                if (value != null && Tag.GetAttribute<BindMineralAttribute>(value) != null) {
                    shortcutType = null;
                    HasShortcut = false;
                } else {
                    shortcutType = value;
                    HasShortcut = true;
                }
            }
        }
        private static UIItem CreateComplexConstructionButton(Type type, ITile tile) {
            CostInfo cost = ConstructionCostBaseAttribute.GetCost(type, tile.GetMap(), true);
            string title = cost.CostType == null ? string.Empty : Localization.Ins.ValPlus(cost.CostType, -cost.RealCostQuantity);

            return new UIItem {
                Interactable = true,
                Type = IUIItemType.Button,
                Content = $"{Localization.Ins.Get<Construct>()}{Localization.Ins.Get(type)} {title}",
                Icon = type.Name,
                OnTap =
                    () => {
                        if (!Globals.SanityCheck()) {
                            return;
                        }

                        IMap map = tile.GetMap();
                        Vector2Int pos = tile.GetPos();

                        ITile newTile = null;
                        if (map.CanUpdateAt(type, pos)) {
                            newTile = map.UpdateAt(type, tile);
                        } else {
                            throw new Exception();
                        }

                        if (newTile != null) {
                            ShortcutMap = map;
                            ShortcutType = type;

                            UI.Ins.Active = false;
                        }

                        //Action action = () => {
                        //    //shortcutSource = shortcutSourceTileType;
                        //    //shortcutTarget = type;

                        //    IMap map = tile.GetMap();
                        //    Vector2Int pos = tile.GetPos();
                        //    ITile newTile = map.UpdateAt(type, pos);
                        //    if (newTile != null) {
                        //        ShortcutMap = map;
                        //        ShortcutType = type;

                        //        UI.Ins.Active = false;
                        //    }
                        //};
                        //action.Invoke();
                    }
                ,
            };
        }

        public static UIItem CreateConstructionButton<T>(ITile tile) {
            return CreateConstructionButton(typeof(T), tile);
        }
        public static UIItem CreateConstructionButton(Type type, ITile tile) {
            return CreateComplexConstructionButton(type, tile);
        }

        public static UIItem CreateTileImage(Type tileType) {
            return new UIItem {
                Type = IUIItemType.Image,
                Content = tileType.Name,
                Scale = 4
            };
        }
        public static UIItem CreateTileImage(string tileType, int scale = 4) {
            return new UIItem {
                Type = IUIItemType.Image,
                Content = tileType,
                Scale = scale
            };
        }
        public static UIItem CreateRawImage(string tileType, int scale = 2) {
            return new UIItem {
                Type = IUIItemType.Image,
                Content = tileType,
                Scale = scale
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