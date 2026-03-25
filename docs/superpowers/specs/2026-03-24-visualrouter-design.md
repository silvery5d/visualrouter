# VisualRouter - VR场馆路线规划可视化工具 设计文档

## 概述

为VR场馆提供2D平面规划工具，用户在网格画布上编辑场馆平面图、导入VR内容配置、拖拽摆放游戏空间（Region），最终导出VR程序可用的配置JSON。交付物为单个exe文件，供内部团队使用。

## 技术栈

- **语言**：Python 3.11+
- **GUI框架**：PySide6 6.6+（QGraphicsScene/QGraphicsView）
- **打包**：PyInstaller --onefile

## 架构

```
┌──────────────────────────────────┐
│        主窗口 (QMainWindow)        │
│  ┌───────────┬─────────────────┐  │
│  │  左侧面板   │    中央画布       │  │
│  │  - 场馆属性  │  QGraphicsView   │  │
│  │  - Region列表│  + 网格背景      │  │
│  │  - 属性编辑  │  + 背景参考图    │  │
│  │            │  + 可交互对象     │  │
│  └───────────┴─────────────────┘  │
│          工具栏 / 状态栏            │
└──────────────────────────────────┘
```

三层解耦：
- **UI层**：Qt窗口、画布、面板
- **交互层**：QGraphicsItem 子类，处理拖拽/旋转/选中
- **数据层**：纯Python数据模型，负责序列化/反序列化JSON

## 画布元素

### 层级（从下到上）

1. 背景参考图（可选，用户导入的场馆照片/图纸）
2. 网格线
3. 墙壁/边界
4. 障碍物（柱子等）
5. Region（含载具标记）

### 元素类型

| 元素 | 形状 | 交互 | 颜色 |
|------|------|------|------|
| 墙壁/边界 | 折线/闭合多边形 | 点击放点，双击/闭合完成 | 黑色 |
| 障碍物 | 矩形/多边形 | 在网格上绘制 | 灰色填充 |
| Region | 多边形边界 | 整体拖拽、旋转 | 半透明彩色，每个Region不同颜色 |
| StartPoint | Region内标记 | 跟随Region | 绿色标记 |
| TargetArea | Region内矩形 | 跟随Region | 橙色标记 |
| 载具 | 固定2.5m x 4.5m矩形 | 跟随Region，不可独立移动 | 蓝色，带方向箭头 |

### 网格系统

- 网格单位对应现实尺寸（默认1格 = 0.5m，可配置）
- 可选吸附到网格（snap to grid）
- 用户可缩放、平移画布

## 工作流程

### 1. 场馆编辑

工具栏模式切换：
- **画墙壁**：点击放点连线，闭合形成场馆边界
- **画障碍物**：拉矩形或点击画多边形
- **选择/移动**：选中元素，拖拽或删除
- 右键菜单：删除、编辑属性
- 可导入背景参考图片，放置在画布最底层

### 2. 导入VR配置

- 从JSON文件导入Region列表
- 导入后所有Region堆叠放置在画布中央，用户逐个拖开
- Region出现在左侧面板列表和画布上
- 每个Region包含：边界多边形、StartPoint、TargetArea、可选载具
- Region颜色自动分配（按顺序轮换：红、蓝、绿、紫、橙...）

### 3. Region摆放

- 拖拽整个Region移动位置
- 旋转Region（鼠标拖拽旋转手柄 或 属性面板输入角度）
- Region内所有子元素（boundary、StartPoint、TargetArea、载具）跟随变换
- Region与障碍物重叠时红色边框警告（利用QGraphicsItem.collidesWithItem()）
- 属性面板可查看/微调坐标数值

### 4. 导出配置

- 导出为VR程序使用的JSON
- 坐标系：以Region1的StartPoint为原点(0,0)，所有坐标为相对偏移

## 数据模型

### 项目文件（.vrproject，JSON格式）

保存完整工作状态，包含场馆数据和Region布局。

```json
{
  "version": 1,
  "venue": {
    "grid_size": 0.5,
    "walls": [
      { "points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 8}, {"x": 0, "y": 8}] }
    ],
    "obstacles": [
      { "name": "柱子1", "type": "polygon", "points": [{"x": 3, "y": 2}, {"x": 3.5, "y": 2}, {"x": 3.5, "y": 2.5}, {"x": 3, "y": 2.5}] }
    ],
    "background_image": "floor_plan.png"
  },
  "region_placements": [
    {
      "region_name": "Region1",
      "canvas_position": {"x": 5.0, "y": 3.0},
      "rotation": 90
    },
    {
      "region_name": "Region2",
      "canvas_position": {"x": 12.0, "y": 3.0},
      "rotation": 0
    }
  ],
  "vr_config_path": "RegionData.json"
}
```

说明：
- `venue` 部分存储场馆平面图数据
- `region_placements` 存储每个Region在画布上的位置和旋转角度
- `vr_config_path` 记录导入的VR配置文件路径
- `background_image` 缺失时静默跳过，不报错
- 背景图使用相对于项目文件的相对路径

### VR配置导入格式（JSON）

所有坐标为Region局部坐标（米），单位与画布一致。

```json
{
  "Regions": [
    {
      "Name": "Region1",
      "boundary": [{"x": 0, "y": 0}, {"x": 3, "y": 0}, {"x": 3, "y": 4}, {"x": 0, "y": 4}],
      "StartPoint": { "position": {"x": 0, "y": 0}, "angle": 0 },
      "TargetArea": { "position": {"x": 2, "y": 3}, "size": {"x": 1, "y": 1} },
      "has_vehicle": true,
      "vehicle": { "relative_position": {"x": 1.5, "y": 2}, "angle": 0 }
    }
  ]
}
```

说明：
- `vehicle.relative_position` 为载具相对于Region局部原点的位置
- `has_vehicle` 为false时不含 `vehicle` 字段

### 导出格式（给VR程序）

坐标系原点 = Region1.StartPoint 的画布位置。
所有坐标通过 `P_export = P_canvas - Region1_StartPoint_canvas` 计算。
角度 = Region导入原始angle + 用户旋转角度。

```json
{
  "Regions": [
    {
      "Name": "Region1",
      "boundary": [{"x": 0, "y": 0}, {"x": 3, "y": 0}, {"x": 3, "y": 4}, {"x": 0, "y": 4}],
      "StartPoint": { "position": {"x": 0, "y": 0}, "angle": 90 },
      "TargetArea": { "position": {"x": 2, "y": 3}, "size": {"x": 1, "y": 1} },
      "vehicle": { "position": {"x": 1.5, "y": 2}, "size": {"x": 2.5, "y": 4.5}, "angle": 90 }
    },
    {
      "Name": "Region2",
      "boundary": [{"x": 5, "y": 0}, {"x": 8, "y": 0}, {"x": 8, "y": 4}, {"x": 5, "y": 4}],
      "StartPoint": { "position": {"x": 5, "y": 0}, "angle": 0 },
      "TargetArea": { "position": {"x": 7, "y": 3}, "size": {"x": 1, "y": 1} },
      "vehicle": { "position": {"x": 6.5, "y": 2}, "size": {"x": 2.5, "y": 4.5}, "angle": 0 }
    }
  ]
}
```

说明：
- 无载具的Region在导出时不含 `vehicle` 字段
- `vehicle.size` 固定为 `{"x": 2.5, "y": 4.5}`，导出时附加供VR程序使用

## 坐标系统与变换

### 画布坐标系
- 原点在画布左上角，X轴向右，Y轴向下
- 单位：米（1单位 = 1米）
- 通过 QGraphicsView 的缩放映射到屏幕像素
- 状态栏实时显示鼠标位置对应的米坐标

### 导入映射
- 导入JSON中的坐标单位为米，直接映射到画布坐标系
- 导入时所有Region堆叠放置在画布中央，用户逐个拖开摆放
- 每个Region的boundary点为相对于Region自身的局部坐标

### 旋转规则
- **旋转中心**：Region边界多边形的几何中心（centroid）
- **角度单位**：度（degrees）
- **方向**：顺时针为正
- **导出角度**：Region导入时的原始angle + 用户在画布上施加的旋转角度

### 导出坐标变换
以Region1的StartPoint画布位置为原点，导出时对每个点做如下变换：

```
P_export = P_canvas - Region1_StartPoint_canvas
```

即：所有导出坐标 = 该点的画布绝对坐标 - Region1 StartPoint的画布绝对坐标。

Region内部各元素（boundary、StartPoint、TargetArea、vehicle）在画布上的绝对坐标已经包含了用户的拖拽偏移和旋转变换。

## 碰撞检测

- Region与障碍物重叠：Region边框变红色警告
- Region与Region重叠：Region边框变红色警告
- Region超出墙壁/场馆边界：Region边框变红色警告
- 利用 QGraphicsItem 的 collidesWithItem() 和 scene boundary 实现

## 撤销/重做

- 使用QUndoStack支持Ctrl+Z / Ctrl+Y

## 常量

- 载具尺寸：2.5m x 4.5m

## 打包

- PyInstaller `--onefile` 生成单个exe
- 背景图片与项目文件保存在同一目录，使用相对路径引用
