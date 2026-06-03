# 角色宿舍 - 程序开发蓝图

## 一、 整体架构概述
本模块为纯客户端表现型系统，无强联网实时同步需求，核心性能瓶颈在于3D场景加载、角色模型换装与家具摆放的实时渲染。后端主要负责玩家宿舍配置数据的持久化存储与校验，所有玩法逻辑（换装、拍照、场景布置）均在客户端本地完成，仅在保存/切换方案、加载场景时与后端通信。系统采用“玩家ID + 角色ID”复合主键，每个角色拥有独立的宿舍配置。

## 二、 前端模块划分 (Client)

### UI 组件层
- **角色选择界面**：横向滑动列表，展示玩家已获取角色头像与名称，支持点击选中。
- **宿舍主场景HUD**：半透明毛玻璃UI，包含换装、姿势、表情、场景布置、拍照、方案保存/切换等入口按钮。
- **换装界面**：网格列表，按部位分类展示可用皮肤/配件，支持实时预览与确认/取消。
- **姿势选择面板**：图标列表，展示已解锁姿势，当前姿势高亮，未解锁显示锁图标。
- **表情选择面板**：图标列表，展示已解锁表情，当前表情高亮，未解锁显示锁图标。
- **场景布置模式UI**：底部家具分类列表，选中后物件跟随移动，支持位置微调、旋转、缩放操作面板。
- **场景模板选择面板**：缩略图列表，展示已解锁模板，当前模板高亮。
- **拍照模式UI**：全屏无UI遮挡，滤镜/特效选择面板（半透明毛玻璃），快门按钮，分享面板。
- **方案保存/切换界面**：命名输入框，方案列表（缩略图展示），支持删除操作。
- **设置面板**：UI透明度滑块（范围 `ui_opacity_min` 至 `ui_opacity_max`），物理效果分级选项。

### 表现层控制器
- **场景加载控制器**：负责加载指定角色的宿舍场景，播放加载动画与进度条，处理加载超时（`scene_load_timeout`秒）与数据损坏重置。
- **角色模型控制器**：管理角色模型的换装、姿势切换（播放过渡动画）、表情切换（面部平滑过渡）。
- **家具放置控制器**：处理物件拖拽、碰撞检测（重叠/边界）、旋转（步进 `rotation_step`度）、缩放（步进 `scale_step`倍）。
- **镜头控制器**：默认第三人称近肩视角，拍照模式自由镜头（双指缩放/旋转，单指平移），支持视角重置。
- **拍照控制器**：隐藏UI，叠加滤镜/特效，截取画面，保存至本地相册（文件名格式 `角色名_时间戳.png`），添加水印（透明度 `watermark_opacity`）。
- **物理系统适配器**：读取玩家全局画质设置，应用对应物理效果分级（高/中/低）。
- **方案缩略图生成器**：方案保存时自动截取场景预览图，用于方案列表展示。

## 三、 后端逻辑划分 (Server)

### 持久化数据 (DB)
- **主表**：`player_character_dormitory`
  - 复合主键：`player_id` (字符串), `character_id` (字符串)
  - 字段：
    - `current_selected_character_id` (字符串，默认空字符串)
    - `character_dormitory_config` (JSON对象，默认空对象)
    - `character_current_skin_id` (字符串，默认空字符串)
    - `character_current_pose_id` (字符串，默认基础姿势ID)
    - `character_current_expression_id` (字符串，默认基础表情ID)
    - `scene_furniture_data` (JSON数组，默认空数组)
    - `scene_template_id` (字符串，默认初始免费模板ID)
    - `character_scheme_data` (JSON数组，默认空数组)
    - `current_scheme_id` (字符串，默认空字符串)
    - `temporary_scheme_data` (JSON对象，默认空对象) — 用于存储未保存的临时方案
    - `temporary_scheme_timestamp` (整数，默认0) — 临时方案最后更新时间戳

### 核心校验逻辑
- **方案保存校验**：
  - 校验方案名称长度不超过 `scheme_name_max_length`。
  - 校验方案名称在当前角色的方案列表中是否重复（返回状态码2）。
  - 校验当前已保存方案数量是否达到 `free_scheme_slot_count`（付费解锁槽位需额外校验付费状态，返回状态码1）。
  - 校验 `character_scheme_data` 中每个方案的数据结构完整性（场景模板ID、家具数据、装扮ID、姿势ID、表情ID必须存在且格式正确）。
- **场景加载校验**：
  - 校验 `character_dormitory_config` 数据完整性，若损坏则重置为默认配置并返回状态码2。
  - 校验 `scene_template_id` 是否在已解锁模板列表中。
  - 校验 `scene_furniture_data` 中每个物件的 `item_id` 是否在玩家背包中。
- **家具放置校验**：
  - 校验当前场景已放置家具数量是否超过 `max_furniture_count`（返回状态码3）。
  - 校验物件放置位置是否超出场景边界（返回状态码2）。
  - 校验物件是否与其他物件或角色重叠（返回状态码1）。
- **换装校验**：
  - 校验 `character_current_skin_id` 是否在玩家背包中且属于该角色可用。
- **姿势/表情校验**：
  - 校验 `character_current_pose_id` / `character_current_expression_id` 是否在已解锁列表中。
- **临时方案保存规则**：
  - **保存时机**：当玩家执行以下任一操作时，系统自动将当前状态保存为临时方案：
    1. 切换方案时，若当前状态与当前方案不一致。
    2. 退出宿舍场景时，若当前状态与当前方案不一致。
    3. 切换角色时，若当前状态与当前方案不一致。
  - **覆盖规则**：临时方案仅保留一份，每次触发保存时覆盖上一次的临时方案。临时方案不占用方案槽位，玩家不可手动删除或重命名。
  - **加载规则**：玩家进入宿舍时，若存在临时方案且与当前方案不一致，弹出提示“检测到未保存的更改，是否恢复？”，选择“是”则加载临时方案，选择“否”则清除临时方案并加载当前方案。

## 四、 前后端通信协议 (API & 数据对接)

- **`Dormitory_LoadScene`**: C->S / 请求参数: `{player_id, character_id}` / 返回参数: `{status_code (scene_load_status枚举), character_dormitory_config, temporary_scheme_data, temporary_scheme_timestamp}`
- **`Dormitory_SaveConfig`**: C->S / 请求参数: `{player_id, character_id, character_dormitory_config}` / 返回参数: `{success: bool}`
- **`Dormitory_SaveScheme`**: C->S / 请求参数: `{player_id, character_id, scheme_name, scheme_data}` / 返回参数: `{status_code (scheme_save_status枚举), scheme_id}`
- **`Dormitory_SwitchScheme`**: C->S / 请求参数: `{player_id, character_id, scheme_id}` / 返回参数: `{status_code, character_dormitory_config}`
- **`Dormitory_DeleteScheme`**: C->S / 请求参数: `{player_id, character_id, scheme_id}` / 返回参数: `{success: bool}`
- **`Dormitory_UpdateFurniture`**: C->S / 请求参数: `{player_id, character_id, scene_furniture_data}` / 返回参数: `{status_code (furniture_placement_status枚举)}`
- **`Dormitory_SaveTemporaryScheme`**: C->S / 请求参数: `{player_id, character_id, temporary_scheme_data}` / 返回参数: `{success: bool, timestamp: int}`
- **`Dormitory_ClearTemporaryScheme`**: C->S / 请求参数: `{player_id, character_id}` / 返回参数: `{success: bool}`
- **`Dormitory_GetUnlockedContent`**: C->S / 请求参数: `{player_id, character_id}` / 返回参数: `{unlocked_skins: [], unlocked_poses: [], unlocked_expressions: [], unlocked_templates: [], unlocked_furniture: [], unlocked_filters: [], unlocked_effects: []}`

## 五、 数值与配置表挂载
程序启动时，读取 `system_numerical_data.json` 中的 `global_parameters` 对象，挂载以下全局参数到内存配置管理器：
- `free_scene_template_count` (整数，默认3)
- `base_pose_count` (整数，默认2)
- `base_expression_count` (整数，默认2)
- `free_filter_count` (整数，默认5)
- `free_scheme_slot_count` (整数，默认3)
- `scene_load_timeout` (整数，默认15)
- `rotation_step` (浮点数，默认15.0)
- `scale_step` (浮点数，默认0.1)
- `max_furniture_count` (整数，默认30)
- `scheme_name_max_length` (整数，默认20)
- `watermark_opacity` (浮点数，默认0.3)
- `ui_opacity_min` (浮点数，默认0.1)
- `ui_opacity_max` (浮点数，默认0.9)

同时读取 `scene_templates`、`base_poses`、`base_expressions`、`free_filters` 等数组，用于初始化免费内容列表。

## 六、 开发优先级与依赖链路 (执行排期) ★ 核心

### 阶段一 (P0 - 底层数据与协议)
- **建表**：创建 `player_character_dormitory` 表，定义复合主键与所有字段。
- **定义API**：完成 `Dormitory_LoadScene`、`Dormitory_SaveConfig`、`Dormitory_SaveScheme`、`Dormitory_SwitchScheme`、`Dormitory_DeleteScheme`、`Dormitory_UpdateFurniture`、`Dormitory_SaveTemporaryScheme`、`Dormitory_ClearTemporaryScheme`、`Dormitory_GetUnlockedContent` 的接口定义与数据结构。
- **后端核心校验逻辑**：实现方案保存校验、场景加载校验、家具放置校验、换装/姿势/表情校验、临时方案保存规则。
- **配置表挂载**：实现 `system_numerical_data.json` 的读取与全局参数初始化。

### 阶段二 (P1 - 前端核心表现)
- **UI框架搭建**：实现角色选择界面、宿舍主场景HUD、换装界面、姿势/表情选择面板、场景布置模式UI、场景模板选择面板、方案保存/切换界面。
- **接入后端API**：前端所有UI操作对接后端API，实现数据的增删改查。
- **核心玩法跑通**：实现角色选择与场景加载、换装、姿势/表情切换、场景布置、场景模板切换、方案保存与切换的完整闭环。
- **拍照模式基础实现**：实现隐藏UI、自由镜头、快门截图、本地保存功能。

### 阶段三 (P2 - 表现层打磨)
- **特效接入**：实现拍照模式滤镜/特效叠加、换装动画、姿势过渡动画、场景模板切换过渡动画。
- **物理系统集成**：实现物理效果分级（高/中/低），适配角色模型物理抖动。
- **UI透明化**：实现UI透明度可调（范围 `ui_opacity_min` 至 `ui_opacity_max`），一键隐藏UI功能。
- **边缘异常兜底**：实现断线重连后的数据同步、加载超时处理、配置数据损坏重置、存储空间不足提示、分享功能异常处理。
- **方案缩略图生成**：实现方案保存时自动截取场景预览图。
- **水印添加**：实现分享截图水印添加（透明度 `watermark_opacity`）。