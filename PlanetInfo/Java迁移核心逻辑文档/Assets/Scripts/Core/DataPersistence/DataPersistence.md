# DataPersistence.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/DataPersistence/DataPersistence.cs`
- 命名空间：`Weathering`
- 代码行数：`383`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `interface IDataPersistence`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `interface IDontSave`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class DataPersistence`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class InventoryData`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `struct MapData`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `struct TileData`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `private Awake()`
- `public WriteSave(string filename, string content)`
- `public DeleteSave(string filename)`
- `public DeleteMap(IMapDefinition map)`
- `public ReadSave(string filename)`
- `public HasSave(string filename)`
- `public SaveGlobals()`
- `public LoadGlobals()`
- `public HasGlobals()`
- `private SerializeVector2(Vector2Int vec)`
- `public SaveMapHead(IMapDefinition map)`
- `public SaveMapBody(IMapDefinition map)`
- `public HasMap(string mapKey)`
- `public LoadMapHead(IMapDefinition map, string mapKey)`
- `public LoadMapBody(IMapDefinition map, string mapKey)`
- `public DeleteSaves()`
- `public DeleteFolder(string directory)`

### 3.2 属性签名

- `public IDataPersistence`
- `public IDontSave`
- `private PersistentBase`
- `private SaveFullPath`
- `public Ins`
- `public InventoryData`
- `public MapData`
- `public TileData`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace Weathering
{
    public interface IDataPersistence
    {
        //bool HasConfig(string name);
        //void WriteConfig(string name, Dictionary<string, string> data);
        //Dictionary<string, string> ReadConfig(string name);

        void WriteSave(string filename, string content);
        string ReadSave(string filename);
        bool HasSave(string filename);

        void SaveMapHead(IMapDefinition map);
        void SaveMapBody(IMapDefinition map);
        void LoadMapHead(IMapDefinition map, string mapKey);
        void LoadMapBody(IMapDefinition map, string mapKey);

        void DeleteMap(IMapDefinition map);

        void SaveGlobals();
        void LoadGlobals();
        bool HasGlobals();

        bool HasMap(string mapKey);

        void DeleteSaves();
    }

    public interface IDontSave
    {
        bool DontSave { get; }
    }

    public class DataPersistence : MonoBehaviour, IDataPersistence
    {
        //public bool HasConfig(string name) {
        //    return File.Exists($"{PersistentBase}{name}{JSON_SUFFIX}");
        //}
        //public void WriteConfig(string name, Dictionary<string, string> data) {
        //    string fullPath = $"{PersistentBase}{name}{JSON_SUFFIX}";
        //    string json = Newtonsoft.Json.JsonConvert.SerializeObject(data, Newtonsoft.Json.Formatting.Indented);
        //    File.WriteAllText(fullPath, json);
        //}
        //public Dictionary<string, string> ReadConfig(string name) {
        //    string fullPath = $"{PersistentBase}{name}{JSON_SUFFIX}";
        //    string json = File.ReadAllText(fullPath);
        //    return Newtonsoft.Json.JsonConvert.DeserializeObject<Dictionary<string, string>>(json);
        //}


        // 存档根目录
        private string PersistentBase { get; set; }
        private const string SavesBase = "Saves/";
        private string SaveFullPath { get; set; }

        private Newtonsoft.Json.JsonSerializerSettings setting = new Newtonsoft.Json.JsonSerializerSettings {
            DefaultValueHandling = Newtonsoft.Json.DefaultValueHandling.Ignore,
        };

        public static IDataPersistence Ins { get; private set; }
        private void Awake() {
            if (Ins != null) throw new Exception();
            Ins = this;

            PersistentBase = Application.persistentDataPath + $"/v{GameConfig.VersionCode}/";
            SaveFullPath = PersistentBase + SavesBase;
            if (!Directory.Exists(SaveFullPath)) {
                Directory.CreateDirectory(SaveFullPath);
            }
        }

        public const string JSON_SUFFIX = ".json";
        public const string TEMP_FILENAME = "temp" + JSON_SUFFIX;
        public void WriteSave(string filename, string content) {
            string tempPath = SaveFullPath + TEMP_FILENAME;
            string targetPath = SaveFullPath + filename + JSON_SUFFIX;
            File.WriteAllText(tempPath, content);
            if (File.Exists(targetPath)) {
                File.Delete(targetPath);
            }
            File.Move(tempPath, targetPath);
        }

        public void DeleteSave(string filename) {
            File.Delete(SaveFullPath + filename + JSON_SUFFIX);
        }
        public void DeleteMap(IMapDefinition map) {
            int width = map.Width;
            int height = map.Height;
            for (int i = 0; i < width; i++) {
                for (int j = 0; j < height; j++) {
                    map.GetTileFast(i, j).OnDestructWithMap();
                }
            }

            string mapKey = map.MapKey;
            if (HasSave(mapKey)) {
                DeleteSave(mapKey);
            }

            string mapHeadKey = map.MapKey + HeadSuffix;
            if (HasSave(mapHeadKey)) {
                DeleteSave(mapHeadKey);
            }
        }


        public string ReadSave(string filename) {
            return File.ReadAllText(SaveFullPath + filename + JSON_SUFFIX);
        }

        public bool HasSave(string filename) {
            return File.Exists(SaveFullPath + filename + JSON_SUFFIX);
        }

        private readonly string globalValuesFilename = "_Globals.Values";
        private readonly string globalRefsFilename = "_Globals.Refs";
        private readonly string globalPrefsFilename = "_Globals.Prefs";
        private readonly string globalInventoryFileName = "_Globals.Inventory";
        public void SaveGlobals() {
            Dictionary<string, ValueData> values = Values.ToData(Globals.Ins.Values);
            Dictionary<string, RefData> refs = Refs.ToData(Globals.Ins.Refs);
            Dictionary<string, string> prefs = Globals.Ins.PlayerPreferences;
            InventoryData inventory = Inventory.ToData(Globals.Ins.Inventory);

            WriteSave(globalValuesFilename, Newtonsoft.Json.JsonConvert.SerializeObject(
                values, Newtonsoft.Json.Formatting.Indented, setting));
            WriteSave(globalRefsFilename, Newtonsoft.Json.JsonConvert.SerializeObject(
                refs, Newtonsoft.Json.Formatting.Indented, setting));
            WriteSave(globalPrefsFilename, Newtonsoft.Json.JsonConvert.SerializeObject(
                prefs, Newtonsoft.Json.Formatting.Indented, setting));
            WriteSave(globalInventoryFileName, Newtonsoft.Json.JsonConvert.SerializeObject(
                inventory, Newtonsoft.Json.Formatting.Indented, setting));
        }

        public void LoadGlobals() {
            Dictionary<string, ValueData> values = Newtonsoft.Json.JsonConvert.DeserializeObject<Dictionary<string, ValueData>>(
                ReadSave(globalValuesFilename), setting);
            Dictionary<string, RefData> refs = Newtonsoft.Json.JsonConvert.DeserializeObject<Dictionary<string, RefData>>(
                ReadSave(globalRefsFilename), setting);
            Dictionary<string, string> prefs = Newtonsoft.Json.JsonConvert.DeserializeObject<Dictionary<string, string>>(
                ReadSave(globalPrefsFilename), setting);
            InventoryData inventory = Newtonsoft.Json.JsonConvert.DeserializeObject<InventoryData>(
                ReadSave(globalInventoryFileName), setting);

            IGlobalsDefinition globals = Globals.Ins as IGlobalsDefinition;
            if (globals == null) throw new Exception();
            globals.ValuesInternal = Values.FromData(values);
            globals.RefsInternal = Refs.FromData(refs);
            globals.PlayerPreferencesInternal = prefs;
            globals.InventoryInternal = Inventory.FromData(inventory);
        }
        public bool HasGlobals() {
            return HasSave(globalValuesFilename) && HasSave(globalRefsFilename);
        }

        public class InventoryData
        {
            public long inventory_quantity;
            public long inventory_capacity;
            public int inventory_type_capacity;
            public Dictionary<string, InventoryItemData> inventory_dict;
        }


        public struct MapData
        {
            public string type;
            public Dictionary<string, ValueData> values;
            public Dictionary<string, RefData> references;

            public InventoryData inventory;
            public InventoryData inventory_of_supply;
        }

        public struct TileData
        {
            public string type;
            public Dictionary<string, ValueData> values;
            public Dictionary<string, RefData> references;

            public InventoryData inventory;
        }

        private string SerializeVector2(Vector2Int vec) => $"{vec.x},{vec.y}";
        //private Vector2Int DeserializeVector2(string s) {
        //    string[] ss = s.Split(',');
        //    int x = int.Parse(ss[0]);
        //    int y = int.Parse(ss[1]);
        //    return new Vector2Int(x, y);
        //}

        public const string HeadSuffix = ".head";

        public void SaveMapHead(IMapDefinition map) {
            // obj => data
            MapData mapHeadData = new MapData {
                type = map.GetType().FullName,
                values = Values.ToData(map.Values),
                references = Refs.ToData(map.Refs),
                inventory = Inventory.ToData(map.Inventory),
                inventory_of_supply = Inventory.ToData(map.InventoryOfSupply),
            };

            // data => json
            string mapHeadJson = Newtonsoft.Json.JsonConvert.SerializeObject(
                mapHeadData, Newtonsoft.Json.Formatting.Indented, setting
            );
            // json => file
            WriteSave(map.MapKey + HeadSuffix, mapHeadJson);
        }
        public void SaveMapBody(IMapDefinition map) {
            // obj => data
            int width = map.Width;
            int height = map.Height;
            Dictionary<string, TileData> mapBodyData = new Dictionary<string, TileData>();
            for (int i = 0; i < width; i++) {
                for (int j = 0; j < height; j++) {
                    ITileDefinition tile = map.Get(i, j) as ITileDefinition;
                    if (tile == null) throw new Exception();

                    if (tile is IDontSave saveOrNot) {
                        if (saveOrNot.DontSave) {
                            continue;
                        }
                    }

                    TileData tileData = new TileData {
                        values = Values.ToData(tile.Values),
                        references = Refs.ToData(tile.Refs),
                        type = tile.GetType().FullName,
                        inventory = Inventory.ToData(tile.Inventory),
                    };

                    mapBodyData.Add(SerializeVector2(new Vector2Int(i, j)), tileData);
                }
            }
            // data => json
            string mapBodyJson = Newtonsoft.Json.JsonConvert.SerializeObject(
                mapBodyData
                 , Newtonsoft.Json.Formatting.Indented, setting
                );
            // json => file
            WriteSave(map.MapKey, mapBodyJson);
        }
        public bool HasMap(string mapKey) {
            return HasSave(mapKey + HeadSuffix);
        }


        public void LoadMapHead(IMapDefinition map, string mapKey) {
            if (map == null) throw new Exception();
            if (mapKey == null) throw new Exception();

            // 1. 读取对应位置json存档
            // file => json
            string mapHeadJson = ReadSave(mapKey + HeadSuffix);

            // 2. 将json反序列化为数据 Dictionary<string, ValueData>, string为数值类型
            // json => data
            MapData mapData = Newtonsoft.Json.JsonConvert.DeserializeObject<MapData>(
                mapHeadJson, setting
            );

            // 3. 从数据中同步到地图对象中
            // data => obj
            //if (!mapData.type.Equals(mapName)) {
            //    throw new Exception("地图存档类型与读取方式不一致");
            //}
            IValues mapValues = Values.FromData(mapData.values);
            if (mapValues == null) throw new Exception();
            map.SetValues(mapValues);

            IRefs mapRefs = Refs.FromData(mapData.references);
            if (mapRefs == null) throw new Exception();
            map.SetRefs(mapRefs);

            IInventory mapInventory = Inventory.FromData(mapData.inventory);
            if (mapInventory == null) throw new Exception();
            map.SetInventory(mapInventory);

            IInventory mapInventoryOfSupply = Inventory.FromData(mapData.inventory_of_supply);
            if (mapInventoryOfSupply == null) throw new Exception();
            map.SetInventoryOfSupply(mapInventoryOfSupply);
        }

        public void LoadMapBody(IMapDefinition map, string mapKey) {
            if (map == null) throw new Exception();
            if (mapKey == null) throw new Exception();

            // 6. 读取对应位置地块json存档
            // file => json
            string mapBodyJson = ReadSave(mapKey);
            // 7. 将json反序列化为数据 Dictionary<string, TileData>, string为位置, TileData包含类型和值
            // json => data
            Dictionary<string, TileData> mapBodyData = Newtonsoft.Json.JsonConvert.DeserializeObject<
                Dictionary<string, TileData>>(mapBodyJson, setting
                );
            // 8. 对于每一个地块, 通过SetTile塞到地图里
            // map => obj
            List<ITileDefinition> tiles = new List<ITileDefinition>(mapBodyData.Count);

            Type defaultTileType = map.DefaultTileType;
            for (int i = 0; i < map.Width; i++) {
                for (int j = 0; j < map.Height; j++) {
                    Vector2Int pos = new Vector2Int(i, j);
                    string key = SerializeVector2(pos);
                    if (mapBodyData.TryGetValue(key, out TileData tileData)) {
                        Type tileType = Type.GetType(tileData.type);

                        ITileDefinition tile = Activator.CreateInstance(tileType) as ITileDefinition;
                        if (tile == null) throw new Exception();
                        tile.Pos = pos;
                        tile.Map = map;
                        tile.TileHashCode = HashUtility.Hash(pos.x, pos.y, map.Width, map.Height, (int)map.HashCode); // HashUtility.Hash((uint)(pos.x + pos.y * map.Width));

                        IValues tileValues = Values.FromData(tileData.values);
                        // if (tileValues == null) throw new Exception();
                        tile.SetValues(tileValues);

                        IRefs tileRefs = Refs.FromData(tileData.references);
                        // if (tileRefs == null) throw new Exception();
                        tile.SetRefs(tileRefs);
                        IInventory inventory = Inventory.FromData(tileData.inventory);
                        // if (inventory == null) throw new Exception();
                        tile.SetInventory(inventory);

                        map.SetTile(pos, tile);
                        tiles.Add(tile);
                    } else {
                        ITileDefinition tile = Activator.CreateInstance(defaultTileType) as ITileDefinition;
                        if (tile == null) throw new Exception();
                        if (tile == null) throw new Exception();
                        tile.Pos = pos;
                        tile.Map = map;
                        tile.TileHashCode = HashUtility.Hash(pos.x, pos.y, map.Width, map.Height, (int)map.HashCode); // HashUtility.Hash((uint)(pos.x + pos.y * map.Width));

                        map.SetTile(pos, tile);
                        tiles.Add(tile);
                    }
                }
            }

            if (tiles.Count != map.Width * map.Height) throw new Exception("存档地图大小与定义不一致");
            foreach (var tile in tiles) {
                tile.NeedUpdateSpriteKeys = true;
                tile.OnEnable();
            }
        }



        public void DeleteSaves() {
            DeleteFolder(SaveFullPath);
        }
        public void DeleteFolder(string directory) {
            foreach (string d in Directory.GetFileSystemEntries(directory)) {
                if (File.Exists(d)) {
                    FileInfo fi = new FileInfo(d);
                    //if (fi.Attributes.ToString().IndexOf("ReadOnly") != -1)
                    //    fi.Attributes = FileAttributes.Normal;
                    fi.Attributes = fi.Attributes & ~(FileAttributes.Archive | FileAttributes.ReadOnly | FileAttributes.Hidden);
                    File.Delete(d);
                } else {
                    DirectoryInfo d1 = new DirectoryInfo(d);
                    if (d1.GetFiles().Length != 0) {
                        DeleteFolder(d1.FullName);
                    }
                    Directory.Delete(d);
                }
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