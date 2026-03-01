# Weathering 插件/模组标准化开发手册（草案）

> 说明：本文聚焦 **主游戏工程结构** 与 addon/mod 标准化方案。  
> 不涉及改动 `PlanetInfo/planet_info.py` 工具实现。

## 1. 项目结构调研结论

### 1.1 顶层目录职责

当前仓库是典型 Unity 工程：

- `Assets/Game`：玩法内容（地块、工业、物流、经济、宇宙地图等）。
- `Assets/Scripts/Core`：核心运行时系统（存档、概念系统、UI、全局状态、数值/引用/背包）。
- `Assets/GameEntry`：游戏启动与主流程入口。
- `Assets/Scenes` / `Assets/Tiles` / `Assets/Sprites` / `Assets/Text`：场景与资源。
- `PlanetInfo`：独立信息工具与文档。

### 1.2 运行时模型

项目当前采用场景单例驱动：

- `GameEntry` 负责读档/创档、切图与入口流程。
- `DataPersistence`、`Globals`、`AttributesPreprocessor`、`MapView`、`UI` 等系统在场景中协作。
- 地图身份依赖字符串 Key（`<Type.FullName>#=x,y=...`）。

优点是开发效率高；问题是对外部模组边界不清晰。

### 1.3 可复用数据抽象

已有接口体系适合作为模组 API 基础：

- `IValue` / `IValues`
- `IRef` / `IRefs`
- `IInventory`
- `IMap` / `ITile`

### 1.4 当前阻碍模组化的关键点

1. 大量依赖 `Type.GetType` / `Activator.CreateInstance` 的反射字符串实例化。
2. 属性预处理默认扫描执行程序集，跨程序集扩展能力弱。
3. 缺乏明确模块边界（尚未 `asmdef` 分层）。
4. 存档字段绑定运行时类型全名，重构/跨包版本兼容风险高。
5. 缺少统一模组生命周期（发现、依赖解析、注册、启停）。

---

## 2. 标准化目标

建立一个“可扩展但可控”的模组协议：

- 第三方可新增地图/地块/概念/配方；
- 不需要修改核心代码即可装载；
- 存档可迁移、加载顺序可预测、错误可隔离。

---

## 3. 建议标准化架构

### 3.1 用 asmdef 划分边界

建议拆分为：

- `Weathering.Core`：接口、基础数据结构、注册中心、序列化契约
- `Weathering.Runtime`：主循环与运行时系统
- `Weathering.Content.BaseGame`：原版内容
- `Weathering.ModKit`：对外 SDK 与模板

第三方模组形态：`Weathering.Mod.<ModName>`。

### 3.2 引入注册中心（替代“自由反射”）

新增注册器：

- `TypeRegistry`
- `TileRegistry`
- `MapRegistry`
- `ConceptRegistry`

统一内容 ID：

- 采用稳定 ID，而非 `Type.FullName`
- 格式建议：`modid:category/name`
- 例：`base:tile/farm`、`expansion:map/dyson_cluster`

### 3.3 采用 manifest 驱动加载

每个模组提供 `mod.json`：

- `id`、`version`、`gameVersion`
- `dependencies`
- `entryType`
- `content` 列表

加载流程：

1. 扫描清单
2. 构建依赖图
3. 解析兼容集合
4. 按拓扑序初始化
5. 注册内容
6. 启动游戏

### 3.4 定义模组生命周期接口

建议接口：

```csharp
public interface IGameMod
{
    void OnPreRegister(IModContext context);
    void OnRegisterContent(IContentRegistry registry);
    void OnPostRegister(IModContext context);
    void OnGameStart(IGameRuntime runtime);
}
```

禁止在静态构造器做隐式注册。

### 3.5 存档协议升级

- 新协议写入 `type_id` + `schema_version` + payload
- 提供迁移钩子：`Migrate(fromVersion, toVersion, data)`
- 保留旧类型名到新 ID 的 alias 映射

### 3.6 内容声明模式

支持两种模式并可混用：

1. 代码优先（行为逻辑）
2. 数据优先（数值、文案、资源映射）

推荐“行为代码 + 数据配置”的混合式。

### 3.7 本地化与资源规范

模组目录建议：

- `Localization/`
- `Sprites/`
- `Audio/`
- `Tiles/`

文案 key 必须命名空间化：

- `myexpansion.tile.quantum_refinery.name`

### 3.8 兼容与容错策略

- API 版本化（`IModApi v1/v2`）
- 冲突检测（重复 ID 默认硬错误）
- 单模组失败隔离（失败可禁用，游戏继续）

---

## 4. 渐进迁移路线（低风险）

### 阶段 1：稳定 ID

- 为内建可扩展类型增加 `ContentId`。
- 增加 `TypeRegistry`，兼容旧存档类型名回退。

### 阶段 2：抽取 Core API

- 把接口与基础契约收敛到 `Core` 稳定程序集。

### 阶段 3：模组加载器

- 实现 `mod.json` 发现 + 依赖解析 + 生命周期驱动。

### 阶段 4：存档协议 v2

- 写入 `type_id`，并提供 v1 -> v2 自动迁移。

### 阶段 5：发布 ModKit

- 提供模板工程、示例模组、验证工具与 CI 规范。

---

## 5. 插件开发者手册（可直接执行）

### 5.1 新建一个模组

1. 创建目录 `Assets/Mods/<ModName>/`
2. 添加 asmdef：`Weathering.Mod.<ModName>`
3. 新建 `mod.json`
4. 实现 `IGameMod` 入口类
5. 注册地图/地块/概念
6. 放置文案与资源
7. 运行验证器并做冷启动测试

### 5.2 开发约束

- 所有可导出内容必须有唯一稳定 ID。
- 尽量依赖接口而不是硬编码具体原版类。
- 不在静态构造中注入玩法。
- 对存档结构做版本管理。

### 5.3 测试清单

- 仅该模组启用时可启动
- 与依赖模组共同启用可启动
- 自定义内容可存档/读档回环
- 模组缺失时有可理解的错误提示
- 缺失文案 key 有回退策略

### 5.4 发布清单

- manifest 校验通过
- 无重复 ID
- 关键文案已本地化
- 存档迁移测试通过
- 更新日志完整

---

## 6. 本仓库下一步建议（优先级）

1. 先上 `TypeRegistry`，新增代码走注册器。
2. 逐步给原版内容补 `ContentId`。
3. 改造 `AttributesPreprocessor` 支持“注册程序集集合扫描”。
4. 增加 `mod.json` 解析与依赖图解析。
5. 增加“模组诊断面板”（已加载/失败原因/冲突信息）。

> 上述 5 步可在不重写既有玩法逻辑的前提下，逐步把项目升级为可持续的 addon/mod 架构。
