# TileResContainer.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/ResConfig/TileResContainer.cs`
- 命名空间：`Weathering`
- 代码行数：`15`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- （未检测到顶层类型声明；请人工确认是否为纯扩展或片段文件）

## 3. 函数/属性接口梳理

- 当前文件无明显方法/属性签名（可能是常量、标记类型或注释占位）。

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Weathering
{
	//public class TileResContainer : MonoBehaviour
	//{
	//	public bool AlsoAsSprite = false;
	//	public List<Tile> Tiles;
	//}
}

```

## 5. Java 迁移建议（本文件）

1. 先保留领域模型（类/接口）结构，再替换底层平台调用。
2. 若含 Unity API（如 `MonoBehaviour`、`Vector2Int`、`Tile`），先在 Java 中定义适配层接口与数据类。
3. 对外部可序列化字段保持字段语义与默认值一致，避免存档语义漂移。
4. 对反射型逻辑优先替换为“注册表 + 稳定 content_id”机制。
5. 将该文件纳入跨语言黄金样例测试，确保行为可回归。