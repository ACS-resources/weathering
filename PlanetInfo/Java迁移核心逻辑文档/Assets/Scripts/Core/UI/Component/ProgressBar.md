# ProgressBar.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/UI/Component/ProgressBar.cs`
- 命名空间：`Weathering`
- 代码行数：`69`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `class ProgressBar`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `public Tap()`
- `public DampTo(float value)`
- `private Awake()`
- `public SetTo(float value)`
- `private Update()`

### 3.2 属性签名

- `public OnTap`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;

namespace Weathering
{
    public class ProgressBar : MonoBehaviour
    {
        public UnityEngine.UI.Slider Slider;

        public UnityEngine.UI.Image Background;
        public UnityEngine.UI.Button Button;

        public UnityEngine.UI.Image Foreground;
        public UnityEngine.UI.Text Text;
        public UnityEngine.UI.Image SliderRaycast;

        public UnityEngine.UI.Image IconImage;

        private Action onTap = null;
        public Action OnTap {
            set {
                onTap = value;
            }
        }
        public void Tap() {
            // 点按钮时
            Sound.Ins.PlayDefaultSound();

            // 在非编辑器模式下, 捕捉报错, 并且
            if (GameMenu.IsInEditor) {
                onTap?.Invoke();
            } else {
                try {
                    onTap?.Invoke();
                } catch (Exception e) {
                    UI.Ins.ShowItems("按钮出现错误! ! ! ", UIItem.CreateText(e.GetType().Name), UIItem.CreateMultilineText(e.Message), UIItem.CreateMultilineText(e.StackTrace));
                    throw e;
                }
            }
        }

        private float velocity = 0;
        private float targetValue = 0;
        public void DampTo(float value) {
            targetValue = value;
            if (Mathf.Abs(value - Slider.value) > 0.5f) {
                SetTo(value);
            }
        }

        private void Awake() {
            SetTo(0);
        }
        public void SetTo(float value) {
            Slider.value = value;
            targetValue = value;
            velocity = 0;
        }
        public float Dampping = 0.05f;
        private void Update() {
            if (Slider.enabled && !Slider.interactable) {
                Slider.value = Mathf.SmoothDamp(Slider.value, targetValue, ref velocity, Dampping);
            }
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