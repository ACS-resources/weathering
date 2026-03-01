# Localization.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/Concept/Localization.cs`
- 命名空间：`Weathering`
- 代码行数：`230`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `interface ILocalization`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Localization`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `private Awake()`
- `public Get(Type key)`
- `public TryGet(Type key)`
- `public GetDescription(Type key)`
- `public ValUnit(Type key)`
- `public Val(Type key, long val)`
- `public ValPlus(Type key, long val)`
- `public Inc(Type key, long val)`
- `public SyncActiveLanguage()`
- `public SwitchNextLanguage()`

### 3.2 属性签名

- `public ILocalization`
- `public Ins`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;

namespace Weathering
{
    public interface ILocalization
    {
        string Get<T>();
        string Get(Type key);

        string TryGet<T>();
        string TryGet(Type key);

        string GetDescription<T>();
        string GetDescription(Type type);

        string ValUnit<T>();
        string ValUnit(Type key);
        //string NoVal(Type key);
        //string NoVal<T>();
        string Val<T>(long val);
        string Val(Type key, long val);
        string ValPlus<T>(long val);
        string ValPlus(Type key, long val);
        string Inc<T>(long val);
        string Inc(Type key, long val);

        void SyncActiveLanguage(); // Globals.Ins.PlayerPreferences[activeLanguageKey]
        void SwitchNextLanguage();
    }

    public class Localization : MonoBehaviour, ILocalization
    {
        public static ILocalization Ins { get; private set; }
        public const string ACTIVE_LANGUAGE = "active_language";
        private void Awake() {
            if (Ins != null) {
                throw new Exception();
            }
            Ins = this;
            if (Globals.Ins.PlayerPreferences.ContainsKey(ACTIVE_LANGUAGE)) {

            } else {
                Globals.Ins.PlayerPreferences.Add(ACTIVE_LANGUAGE, DefaultLanguage);
            }
            SyncActiveLanguage();
        }


        private string DefaultLanguage = "zh_cn";


        public string[] SupporttedLanguages;

        [SerializeField]
        private TextAsset[] Jsons;
        private Dictionary<string, string> Dict;
        private Dictionary<string, string> DictOfDescription;

        public string Get<T>() {
            return Get(typeof(T));
        }
        public string Get(Type key) {
            if (Dict.TryGetValue(key.FullName, out string result)) {
                // throw new Exception($"localization key not found: {key}");
                // return string.Format(result, "");
                return result;
            }
            return key.FullName;
        }
        public string TryGet<T>() {
            return TryGet(typeof(T));
        }

        public string TryGet(Type key) {
            if (Dict.TryGetValue(key.FullName, out string result)) {
                // throw new Exception($"localization key not found: {key}");
                // return string.Format(result, "");
                return result;
            }
            return null;
        }

        public string GetDescription<T>() {
            return GetDescription(typeof(T));
        }

        public const string DescriptionSuffix = "#Description";
        public string GetDescription(Type key) {
            if (DictOfDescription.TryGetValue(key.FullName, out string result)) {
                return result;
            }
            return null;
        }


        public string ValUnit<T>() {
            return ValUnit(typeof(T));
        }
        public string ValUnit(Type key) {
            if (Dict.TryGetValue(key.FullName, out string result)) {
                return string.Format(result, "");
            }
            return key.FullName;
        }



        public string Val<T>(long val) {
            return Val(typeof(T), val);
        }
        public string Val(Type key, long val) {
            if (key == null) throw new Exception();
            if (Dict.TryGetValue(key.FullName, out string result)) {
                // throw new Exception($"localization key not found: {key}");
                if (val > 0) {
                    return string.Format(result, $" {val}");
                } else if (val < 0) {
                    return string.Format(result, $"-{-val}");
                } else {
                    return string.Format(result, " 0");
                }
            }
            return key.FullName;
        }
        public string ValPlus<T>(long val) {
            return ValPlus(typeof(T), val);
        }
        public string ValPlus(Type key, long val) {
            if (Dict.TryGetValue(key.FullName, out string result)) {
                // throw new Exception($"localization key not found: {key}");
                if (val > 0) {
                    return string.Format(result, $"+{val}");
                } else if (val < 0) {
                    return string.Format(result, $"-{-val}");
                } else {
                    return string.Format(result, " 0");
                }
            }
            return key.FullName;
        }

        public string Inc<T>(long val) {
            return Inc(typeof(T), val);
        }
        public string Inc(Type key, long val) {
            if (Dict.TryGetValue(key.FullName, out string result)) {
                // throw new Exception($"localization key not found: {key}");
                if (val > 0) {
                    return string.Format(result, $" Δ{val}");
                } else if (val < 0) {
                    return string.Format(result, $"-Δ{-val}");
                } else {
                    return string.Format(result, " 0");
                }
            }
            return key.FullName;
        }

        public void SyncActiveLanguage() {
            string activeLanguage = Globals.Ins.PlayerPreferences[ACTIVE_LANGUAGE];
            bool found = false;

            Dict = new Dictionary<string, string>();
            DictOfDescription = new Dictionary<string, string>();
            foreach (var jsonTextAsset in Jsons) {
                if (jsonTextAsset.name.StartsWith(activeLanguage)) {
                    Dictionary<string, string> subDict = Newtonsoft.Json.JsonConvert.DeserializeObject<Dictionary<string, string>>(jsonTextAsset.text);
                    foreach (var pair in subDict) {
                        if (Dict.ContainsKey(pair.Key)) {
                            UIPreset.Throw($"出现了重复的key “{pair.Key}” in {jsonTextAsset.name}. 不知道另一个key在哪个文件");
                        }
                        else {
                            int indexOfHashMark = pair.Key.IndexOf('#');
                            if (indexOfHashMark < 0) {
                                Dict.Add(pair.Key, pair.Value);
                            } 
                            else {
                                string typeName = pair.Key.Substring(0, indexOfHashMark);
                                //if (DictOfDescription.ContainsKey(typeName)) {
                                //    Debug.LogError(typeName);
                                //}
                                DictOfDescription.Add(typeName, pair.Value);
                            }
                        }
                    }
                    found = true;
                }
            }
            if (!found) {
                throw new Exception(activeLanguage);
            }
        }

        public void SwitchNextLanguage() {
            if (SupporttedLanguages.Length == 1) {
                UIPreset.Notify(null, "只有一种语言配置");
                return;
            }
            string activeLanguage = Globals.Ins.PlayerPreferences[ACTIVE_LANGUAGE];

            // 找到下一个语言, 效率很低, 但可以用
            bool found = false;
            int index = 0;
            foreach (var jsonTextAsset in SupporttedLanguages) {
                if (jsonTextAsset == activeLanguage) {
                    // Dict = Newtonsoft.Json.JsonConvert.DeserializeObject<Dictionary<string, string>>(jsonTextAsset.text);
                    found = true;
                    break;
                }
                index++;
            }
            if (!found) throw new Exception();
            index++;
            if (index == Jsons.Length) {
                index = 0;
            }

            // Dict = Newtonsoft.Json.JsonConvert.DeserializeObject<Dictionary<string, string>>(Jsons[index].text);

            Globals.Ins.PlayerPreferences[ACTIVE_LANGUAGE] = Jsons[index].name;
            SyncActiveLanguage();
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