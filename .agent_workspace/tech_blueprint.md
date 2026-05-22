好的，老板。收到您的详细设计案、数值配置表及系统Schema骨架。作为项目高级主程序，我将严格遵循您的指示，输出一份严谨、可落地的【程序开发蓝图 (Tech Blueprint)】。

---

# 【角色私人宿舍】系统 - 程序开发蓝图 (Tech Blueprint)

## 一、 整体架构概述

本模块为**单机弱联网**的付费内容包，核心性能瓶颈在于**客户端**的3D渲染与交互表现。

- **技术定位**：一个独立的、可选的、以情感羁绊为核心的3D互动场景系统。它不依赖实时对战或强同步逻辑，但需要与后端进行数据读写（解锁状态、好感度、皮肤列表）。
- **核心挑战**：
    1.  **客户端性能**：高精度角色模型、软体物理、流畅的视角控制与动画过渡，对移动端设备性能要求较高。
    2.  **数据隔离**：宿舍好感度系统必须与主好感度系统完全独立，避免数据污染。
    3.  **边界处理**：支付断线、小游戏断线、好感度解锁事件延迟触发等异常场景的兜底逻辑。

## 二、 前端模块划分 (Client)

### 1. UI 组件层
- **`DormitoryEntryWidget`**：主界面“基地”入口的子选项。负责显示“宿舍”按钮、`¥68`标签（未解锁时）、以及“需拥有五星角色”的置灰/隐藏状态。
- **`UnlockPurchasePanel`**：购买“私人宿舍钥匙”的弹窗。包含商品详情、价格、支付按钮。支付成功后触发解锁特效。
- **`RoleSelectPanel`**：已解锁五星角色的列表界面。支持滑动选择，点击后加载对应宿舍场景。
- **`DormitoryHUD`**：宿舍场景内的半透明UI。包含：
    - 右上角：好感度进度条及等级显示。
    - 右侧：`服装`、`姿势`、`小游戏` 按钮。
    - 操作提示（5秒后淡出）。
- **`SkinSelectPanel`**：服装切换弹窗，展示已解锁皮肤列表。
- **`PoseSelectPanel`**：姿势切换弹窗，展示预设动作列表。
- **`MinigameEntryPanel`**：小游戏入口及选择界面。
- **`MinigamePanel`**：猜拳/拍手游戏的核心交互界面。
- **`UnlockNotificationPanel`**：好感度升级或解锁新内容时的特效与提示弹窗。
- **`AffectionFloatingText`**：好感度增加时的浮动提示（“好感度 +X”）。
- **`InteractionCooldownIndicator`**：互动冷却期间，屏幕边缘的红光闪烁提示。

### 2. 表现层控制器
- **`DormitorySceneController`**：场景核心控制器。负责：
    - 加载/卸载角色模型、场景资源。
    - 管理第一人称摄像机（旋转、缩放、互动特写）。
    - 播放“开门动画”。
    - 管理角色状态机（待机、互动、小游戏、胜利/失败动画）。
    - 接收UI层指令，调用角色表现接口。
- **`CharacterInteractionController`**：角色互动表现控制器。负责：
    - 射线检测点击区域，判断是否为“可互动区域”或“禁区”。
    - 调用动画系统播放对应互动动画（如摸头、后退摇头）。
    - 调用语音系统播放对应语音，并显示字幕。
    - 管理互动冷却计时器（本地计时，服务端校验）。
    - 触发软体物理（如胸部、头发抖动）。
- **`MinigameController`**：小游戏逻辑控制器。负责：
    - 实现猜拳/拍手游戏的本地逻辑（AI对手）。
    - 判定胜负，播放胜利/失败动画。
    - 调用Live2D播放器播放专属剧情片段。
- **`SkinController`**：皮肤切换控制器。负责：
    - 根据玩家选择的皮肤ID，动态替换角色模型。
    - 触发布料物理重新结算。
- **`AffectionController`**：好感度表现控制器。负责：
    - 监听好感度变化事件，驱动UI进度条和浮动提示。
    - 监听好感度等级变化事件，触发解锁通知。

## 三、 后端逻辑划分 (Server)

### 1. 持久化数据 (DB)
- **`player_dormitory` 表**：
    - `player_id` (主键)
    - `dormitory_unlocked` (bool, 默认false)
- **`player_dormitory_affection` 表**：
    - `player_id` (联合主键)
    - `role_id` (联合主键)
    - `affection_value` (int, 范围0-1000)
    - `unlocked_interactions` (JSON数组, 存储已解锁的互动ID列表)
    - `unlocked_voice_lines` (JSON数组, 存储已解锁的语音ID列表)
- **`player_dormitory_minigame` 表**：
    - `player_id` (联合主键)
    - `role_id` (联合主键)
    - `weekly_reset_timestamp` (int, 记录本周一凌晨4点的时间戳，用于判断是否已进行)
    - `last_result` (string, 枚举: “win”, “lose”, “disconnect”)

### 2. 核心校验逻辑
- **`unlock_dormitory` 接口**：
    - **校验**：`dormitory_unlocked` 必须为 `false`；支付订单必须有效且未使用。
    - **防作弊**：必须通过支付SDK的回调验证订单，严禁客户端直接调用解锁。
- **`add_dormitory_affection` 接口**：
    - **校验**：`dormitory_unlocked` 必须为 `true`；`affection_value` 增加后不能超过1000；`interaction_cooldown` 必须已过期（服务端记录上次互动时间戳）。
    - **防作弊**：限制单次增加上限（如50点）；限制单位时间内调用频率（如每分钟最多10次）。
- **`minigame_result` 接口**：
    - **校验**：`weekly_reset_timestamp` 必须早于本周一凌晨4点（即本周未进行）；`minigame_result` 不能为 `disconnect`（断线重连场景）。
    - **防作弊**：结果必须由服务端生成（猜拳AI逻辑在服务端执行），客户端仅上传操作序列，服务端判定胜负。
- **`get_dormitory_interaction_list` 接口**：
    - **校验**：根据 `affection_value` 计算当前等级，查询 `unlocked_interactions` 和 `unlocked_voice_lines`，返回当前等级可用的所有互动。

## 四、 前后端通信协议 (API & 数据对接)

| 接口名 | 方向 | 请求参数 | 返回参数 |
| :--- | :--- | :--- | :--- |
| `is_dormitory_unlocked` | C->S | `player_id` | `{ unlocked: bool }` |
| `unlock_dormitory` | C->S | `player_id`, `payment_order_id` | `{ success: bool, error_code: int }` |
| `get_owned_five_star_roles` | C->S | `player_id` | `{ role_ids: [string] }` (复用已有接口) |
| `get_dormitory_affection` | C->S | `player_id`, `role_id` | `{ affection_value: int }` |
| `add_dormitory_affection` | C->S | `player_id`, `role_id`, `value: int` | `{ new_affection_value: int, unlocked_items: { interactions: [string], voice_lines: [string] } }` |
| `get_dormitory_interaction_list` | C->S | `player_id`, `role_id` | `{ interactions: [{ interaction_id: string, voice_id: string }] }` |
| `get_unlocked_skins` | C->S | `player_id`, `role_id` | `{ skin_ids: [string] }` (复用已有接口) |
| `minigame_start` | C->S | `player_id`, `role_id` | `{ success: bool, error_code: int }` |
| `minigame_submit_action` | C->S | `player_id`, `role_id`, `round: int`, `action: string` | `{ round_result: string, ai_action: string }` |
| `minigame_end` | C->S | `player_id`, `role_id`, `final_result: string` | `{ affection_gained: int, unlocked_cutscene_id: string (optional) }` |
| `get_dormitory_voice_pool` | C->S | `role_id`, `affection_level: int` | `{ voice_ids: [string] }` |

## 五、 数值与配置表挂载

程序启动时，需加载数值策划提供的 `system_numerical_data.json` 文件，并解析以下关键配置：

1.  **好感度等级阈值**：
    - 从 `implementation_notes` 中提取 `affection_level_thresholds` 数组：`[0, 50, 120, 210, 320, 450, 600, 770, 960, 1000]`。
    - 用于服务端计算当前等级，以及客户端显示进度条。
2.  **互动冷却时间**：
    - 从 `field_dictionary` 中提取 `interaction_cooldown` 的默认值 `5.0`。
    - 用于客户端本地计时和服务端校验。
3.  **互动区域配置**：
    - 需要一份独立的 `interaction_zone_config.json` 配置文件（非本数值文档提供），定义每个角色模型的骨骼名称与对应的互动区域类型（可互动/禁区）。
4.  **小游戏配置**：
    - 需要一份 `minigame_config.json` 配置文件，定义猜拳/拍手游戏的规则、AI难度、胜利/失败动画ID等。

## 六、 开发优先级与依赖链路 (执行排期) ★ 核心

### 阶段一 (P0 - 底层数据与协议) - 预估耗时：2周
- **目标**：打通数据链路，确保核心逻辑可被服务端验证。
- **任务**：
    1.  **数据库建表**：创建 `player_dormitory`, `player_dormitory_affection`, `player_dormitory_minigame` 三张表。
    2.  **核心API定义与实现**：
        - `is_dormitory_unlocked`
        - `unlock_dormitory` (含支付校验逻辑)
        - `add_dormitory_affection` (含冷却校验、频率限制)
        - `get_dormitory_interaction_list` (含等级计算逻辑)
    3.  **小游戏服务端逻辑**：实现猜拳AI，完成 `minigame_start`, `minigame_submit_action`, `minigame_end` 接口。
    4.  **数值配置表加载**：实现 `system_numerical_data.json` 的解析与缓存。

### 阶段二 (P1 - 前端核心表现与玩法闭环) - 预估耗时：4周
- **目标**：实现完整的用户交互流程，核心玩法可玩。
- **任务**：
    1.  **UI框架搭建**：完成所有UI面板的Prefab制作与基础逻辑。
    2.  **场景与角色加载**：实现 `DormitorySceneController`，完成场景切换、角色模型加载。
    3.  **自由观赏模式**：实现第一人称摄像机控制（旋转、缩放）、服装/姿势切换。
    4.  **核心互动模式**：实现 `CharacterInteractionController`，完成射线检测、动画播放、语音播放、冷却逻辑。
    5.  **小游戏前端**：实现 `MinigameController`，完成猜拳/拍手游戏的UI与逻辑，接入服务端API。
    6.  **好感度系统前端**：实现 `AffectionController`，完成进度条、浮动提示、解锁通知。
    7.  **前后端联调**：将所有P0接口与前端表现串联，跑通“解锁 -> 进入 -> 互动 -> 小游戏 -> 好感度升级”的完整闭环。

### 阶段三 (P2 - 表现层打磨与边缘异常兜底) - 预估耗时：2周
- **目标**：提升品质，处理所有边界情况，确保稳定性。
- **任务**：
    1.  **表现层特效接入**：
        - 购买解锁特效。
        - 好感度升级解锁特效。
        - 小游戏胜利/失败动画。
        - 互动时的镜头特写与软体物理。
    2.  **边缘异常兜底**：
        - **支付断线**：实现订单验证与补发机制。
        - **小游戏断线**：实现幂等逻辑，允许重试。
        - **好感度升级断线**：实现登录时自动触发解锁事件。
        - **网络中断**：场景加载中断时，显示重连提示并返回主界面。
        - **性能优化**：提供“关闭开门动画”和“关闭软体物理”选项。
    3.  **资源与配置表最终检查**：确保所有互动动作、语音、皮肤ID与配置表一致，无遗漏。