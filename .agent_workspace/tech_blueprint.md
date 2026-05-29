# 温泉中心 - 程序开发蓝图

## 一、 整体架构概述
温泉中心是宿舍系统的扩展场景模块，属于**弱联网、强表现**的休闲陪伴系统。核心性能瓶颈在于：角色模型（泳装/浴巾+湿发效果）的实时渲染、水面物理模拟与蒸汽粒子特效的叠加，以及小游戏（射线检测/拖拽物理）的即时响应。所有玩法逻辑（角色刷新、小游戏胜负判定、奖励解锁）均需在服务端完成校验，前端主要负责表现层渲染与用户交互反馈。

## 二、 前端模块划分 (Client)

### UI 组件层
- **温泉入口按钮**：位于宿舍场景，根据 `dormitory_hotspring_unlocked` 控制显隐，根据角色池数量控制置灰状态。
- **主场景 HUD**：包含角色信息栏、换人按钮、小游戏入口按钮（水枪射击/捞水球）、货币显示、UI 隐藏切换按钮。
- **小游戏界面**：
  - 水枪射击：准星、计时器、得分板、跳过弹窗。
  - 捞水球：拖拽操作区、计时器、进度条、跳过弹窗。
- **奖励解锁弹窗**：展示解锁内容预览（表情/语音/动作名称与缩略图），播放解锁特效。
- **纯观赏模式**：一键隐藏所有 UI 的切换状态。

### 表现层控制器
- **场景与运镜控制器**：
  - 默认第三人称近肩视角（`camera_mode = hotspring_default`），支持旋转/缩放，限制最低角度。
  - 小游戏触发时自动推近至面部特写（`camera_mode = minigame_closeup`），结束后平滑复位。
- **角色动画控制器**：
  - 管理角色入水/出水动画、被水花溅到的后仰/躲闪动画、小游戏反馈动画（开心鼓掌/惊讶害羞）。
  - 根据 `character_current_skin_id` 加载对应泳装/浴巾模型，启用湿发效果。
- **物理与特效播放器**：
  - 水面波纹/涟漪系统（角色移动/互动时触发）。
  - 水花溅射特效（靶子/水球被击中时播放）。
  - 蒸汽粒子特效（场景常驻）。
  - 物理骨骼抖动（头发、浴巾边缘）。
  - 性能降级方案：关闭水面粒子特效，物理效果切换为预设动画。

## 三、 后端逻辑划分 (Server)

### 持久化数据 (DB)
- **玩家全局存档**：
  - `last_hotspring_entry_timestamp`：上次进入时间戳。
  - `dormitory_hotspring_unlocked`：温泉中心解锁状态。
  - `daily_special_character_used`：今日特惠角色是否已使用。
  - `daily_free_refresh_count`：当日免费刷新次数。
  - `daily_minigame_reward_count`：当日小游戏奖励已领取次数。
  - `current_hotspring_character_id`：当前场景角色 ID。
  - `minigame_active`：小游戏是否进行中。
  - `minigame_type`：当前小游戏类型（shooting/fishing）。
  - `minigame_snapshot`：断线重连时保存的游戏状态快照。
  - `minigame_failure_count`：当前小游戏类型下的连续失败次数。
  - `character_hotspring_rewards_unlocked`：每个角色已解锁的奖励 ID 列表（数组）。
  - `character_hotspring_interaction_record`：互动次数统计（仅记录，不产出经验）。

### 核心校验逻辑
- **角色刷新校验**：
  - 检查 `daily_special_character_used` 是否已使用，若已使用则不再触发特惠角色。
  - 检查 `daily_free_refresh_count` 是否超过 `DAILY_FREE_REFRESH_LIMIT`，若超过则校验 `player_base_currency` 是否足够扣除 `REFRESH_CURRENCY_COST`。
  - 校验角色池是否为空（玩家拥有角色数量 > 0）。
- **小游戏校验**：
  - 校验 `daily_minigame_reward_count` 是否已达 `DAILY_MINIGAME_REWARD_LIMIT`。
  - 校验当前角色奖励池是否已全部解锁。
  - 小游戏开始/结束状态机校验（防止重复开始或异常结束）。
  - 命中数/捞取数统计的实时校验（防止前端篡改数据）。
  - 跳过条件校验：`minigame_failure_count` 是否 >= `FAILURE_THRESHOLD`，以及 `player_base_currency` 是否足够扣除 `SKIP_CURRENCY_COST`。
- **奖励解锁校验**：
  - 校验命中数/捞取数是否达标（>= `SHOOTING_SUCCESS_THRESHOLD` / `FISHING_SUCCESS_THRESHOLD`）。
  - 校验奖励池中是否存在未解锁奖励。
  - 校验 `daily_minigame_reward_count` 是否已达上限。
- **异常行为日志**：记录所有尝试通过非正常手段获取战斗数值/抽卡资源的操作。

## 四、 前后端通信协议 (API & 数据对接)

- **`EnterHotSpring`**: C->S / `{}` / `{ current_character_id, daily_special_available, daily_free_refresh_count, daily_minigame_reward_count, player_base_currency }`
- **`RefreshCharacter`**: C->S / `{}` / `{ new_character_id, updated_daily_free_refresh_count, updated_player_base_currency }`
- **`StartMinigame`**: C->S / `{ minigame_type: string }` / `{ minigame_snapshot, game_time_limit }`
- **`MinigameHit`**: C->S / `{ hit_count_increment: int }` / `{ current_hit_count, updated_minigame_snapshot }`
- **`MinigameEnd`**: C->S / `{}` / `{ is_success: bool, reward_unlocked_id (optional), updated_daily_minigame_reward_count, updated_minigame_failure_count }`
- **`SkipMinigame`**: C->S / `{}` / `{ reward_unlocked_id, updated_player_base_currency, updated_daily_minigame_reward_count }`
- **`ExitMinigame`**: C->S / `{}` / `{ minigame_active: false, minigame_failure_count: 0 }`
- **`GetCharacterRewardStatus`**: C->S / `{ character_id: string }` / `{ unlocked_rewards: array, all_unlocked: bool }`
- **`ToggleUI`**: C->S / `{ new_state: string }` / `{ ui_visibility_state }`
- **`UpdateCameraMode`**: C->S / `{ new_mode: string }` / `{ camera_mode }`

## 五、 数值与配置表挂载

程序启动时，从 `system_numerical_data.json` 中读取以下常量配置。**注意：** 系统策划案中以占位符形式出现的数值（如 `[REFRESH_CURRENCY_COST]`）在数值配表和说明书中均未定义具体数值。程序在开发阶段需将这些占位符作为**待定参数**处理，由数值策划后续补充完整后，再挂载到配置表中。当前阶段，程序应使用默认占位值（如 0 或空字符串）进行开发，并预留配置读取接口。

- **从 `field_dictionary` 读取**：
  - `DAILY_FREE_REFRESH_LIMIT`：对应 `daily_free_refresh_count` 的取值范围上限（默认值 0，需数值策划补充）。
  - `DAILY_MINIGAME_REWARD_LIMIT`：对应 `daily_minigame_reward_count` 的取值范围上限（默认值 0，需数值策划补充）。
  - `TARGET_COUNT`：对应 `current_game_hit_count` 的取值范围上限（默认值 0，需数值策划补充）。
  - `BALL_COUNT`：对应 `current_game_ball_count` 的取值范围上限（默认值 0，需数值策划补充）。
- **从 `implementation_notes` 读取**：
  - 所有布尔类型字段的连续公式规则（base=0, growth=0, type='linear'）。
  - 所有整数类型字段的连续公式规则（base=0, growth=1, type='linear'）。
- **待定参数（需数值策划补充）**：
  - `REFRESH_CURRENCY_COST`：主动换人消耗的基础货币数量。
  - `SHOOTING_TIME_LIMIT`：水枪射击小游戏倒计时秒数。
  - `SHOOTING_SUCCESS_THRESHOLD`：水枪射击成功所需命中数。
  - `FISHING_TIME_LIMIT`：捞水球小游戏倒计时秒数。
  - `FISHING_SUCCESS_THRESHOLD`：捞水球成功所需捞取数。
  - `FAILURE_THRESHOLD`：触发跳过选项所需的连续失败次数。
  - `SKIP_CURRENCY_COST`：跳过小游戏消耗的基础货币数量。
  - `MIN_REWARD_SLOTS`：每个角色在温泉中心的最小奖励槽位数。

## 六、 开发优先级与依赖链路 (执行排期) ★ 核心

### 阶段一 (P0 - 底层数据与协议)
- **建表**：在玩家全局存档中创建温泉中心相关字段（`last_hotspring_entry_timestamp`, `daily_special_character_used`, `daily_free_refresh_count`, `daily_minigame_reward_count`, `current_hotspring_character_id`, `minigame_active`, `minigame_type`, `minigame_snapshot`, `minigame_failure_count`, `character_hotspring_rewards_unlocked`）。
- **定义 API**：完成所有前后端通信接口的协议定义（请求/返回参数）。
- **后端核心校验逻辑**：
  - 实现角色刷新校验（特惠角色、免费次数、货币消耗）。
  - 实现小游戏状态机（开始、命中、结束、退出、跳过）的校验逻辑。
  - 实现奖励解锁校验（达标判定、奖励池检查、每日上限）。
  - 实现异常行为日志记录。

### 阶段二 (P1 - 前端核心表现)
- **UI 框架搭建**：
  - 实现温泉入口按钮（显隐/置灰逻辑）。
  - 实现主场景 HUD（角色信息、换人按钮、小游戏入口、货币显示、UI 隐藏切换）。
  - 实现小游戏界面（水枪射击准星/计时器/得分板、捞水球拖拽区/计时器/进度条）。
  - 实现奖励解锁弹窗。
- **接入后端 API**：前端所有交互按钮/操作绑定对应的后端接口调用。
- **核心玩法跑通**：
  - 角色刷新流程（进入场景 -> 请求角色 -> 显示角色模型）。
  - 小游戏完整流程（开始 -> 操作 -> 命中/捞取 -> 结束 -> 奖励解锁）。
  - 跳过选项流程（失败次数达标 -> 弹窗 -> 消耗货币 -> 解锁奖励）。

### 阶段三 (P2 - 表现层打磨)
- **特效接入**：
  - 水面波纹/涟漪系统。
  - 水花溅射特效。
  - 蒸汽粒子特效。
  - 角色物理抖动（头发、浴巾）。
- **运镜与动画**：
  - 默认第三人称近肩视角（旋转/缩放/角度限制）。
  - 小游戏面部特写推近/复位动画。
  - 角色入水/出水动画、被溅到反应动画、小游戏反馈动画。
- **边缘异常兜底**：
  - 断线重连：`minigame_snapshot` 的保存与恢复逻辑。
  - 性能降级：设备性能不足时关闭水面粒子特效，物理效果切换为预设动画。
  - 空角色池/奖励池已满/货币不足等 UI 提示与按钮置灰逻辑。
  - 纯观赏模式（一键隐藏 UI）的切换与恢复。