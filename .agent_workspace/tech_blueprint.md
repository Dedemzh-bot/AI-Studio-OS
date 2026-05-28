# 角色私人宿舍 - 程序开发蓝图

## 一、 整体架构概述
本模块为“角色私人宿舍”系统，属于强客户端表现、弱服务端校验的混合架构。核心性能瓶颈在于3D房间场景加载、互动动画播放与AI行为状态机切换。服务端主要负责持久化玩家数据（好感度、解锁状态、冷却时间等）与防作弊校验（每日上限、冷却逻辑）。前后端通过RESTful API通信，断线重连时需恢复房间状态与AI行为。

## 二、 前端模块划分 (Client)

### UI 组件层
- **角色选择界面**：展示已解锁角色列表（灰色锁图标表示未解锁），点击进入对应房间。
- **房间主界面**：3D场景渲染、视角控制（旋转/缩放/平移）、互动热点高亮与点击、AI行为播放。
- **互动热点UI**：热点高亮微光+提示文字、冷却遮罩+倒计时、未解锁提示（好感度等级不足）。
- **小游戏界面**：规则说明、游戏HUD（分数/时间）、结算界面（奖励展示）。
- **好感度UI**：经验条动画（左上角）、升级特效（角色剪影+光效）、解锁内容提示框。
- **剧情播放界面**：全屏Live2D/3D演出、暂停/快进/跳过按钮。
- **纪念品摆放界面**：装饰模式（拖拽摆放）、半透明预览、固定后点击查看。
- **拍照模式界面**：滤镜选择、姿势/表情切换、拍照按钮、截图保存提示。
- **付费弹窗**：DLC购买弹窗（名称/价格/内容简介）、支付成功/失败提示。
- **加载与错误提示**：加载中动画（角色剪影+进度条）、错误提示弹窗（资源损坏/断线等）。

### 表现层控制器
- **场景加载控制器**：根据角色ID加载对应3D房间场景（资源路径由 `character_room_map` 表定义），加载完成设置 `room_loaded_flag = true`。
- **视角控制器**：触摸/鼠标拖拽旋转、双指/滚轮缩放，限制在房间边界内，拍照模式额外支持平移。
- **互动热点控制器**：检测玩家视线与热点距离（3米内），高亮显示（微光+粒子效果），点击后触发动画播放。
- **动画播放器**：播放互动动画（含第一人称/近景特写运镜），播放期间UI自动隐藏（仅保留退出按钮）。
- **AI行为状态机**：定时器（30-60秒随机）切换角色行为（看书/发呆/做家务/哼歌），行为切换平滑过渡，随机触发语音。
- **特效播放器**：好感度升级光效、解锁内容提示框动画、拍照快门音效、购买成功解锁特效。
- **断线重连控制器**：断线时保持房间场景加载，重连后恢复AI行为ID与互动状态。

## 三、 后端逻辑划分 (Server)

### 持久化数据 (DB)
- **角色房间数据**：
  - `room_config_data`（浮点数数组）：房间配置数据，包含房间ID、角色ID等。
  - `furniture_layout`（浮点数数组）：家具布局数据，包含家具位置、旋转等。
  - `decoration_placement`（浮点数数组）：装饰品摆放数据，包含装饰品位置、旋转等。
  - `room_state`（整数）：房间状态码（0=未加载，1=加载中，2=已加载，3=互动中，4=拍照模式）。
- **互动热点数据**：
  - `hotspot_interaction_count`（整数）：热点互动次数。
  - `last_interaction_timestamp`（浮点数）：上次互动时间戳。
  - `cooldown_timer`（浮点数）：冷却计时器，记录热点冷却结束时间戳（用于服务端校验冷却状态）。
  - `unlock_affection_level_requirement`（整数）：解锁所需好感度等级。
  - `hotspot_unlocked_flag`（布尔值）：热点解锁标志。
  - `hotspot_on_cooldown`（布尔值）：热点冷却标志。
- **小游戏数据**：
  - `daily_play_count`（整数）：每日游玩次数。
  - `max_daily_play_count`（整数）：每日最大游玩次数（默认100）。
  - `score_record`（浮点数数组）：得分记录。
  - `highest_score`（浮点数）：最高得分。
  - `play_count`（整数）：游玩总次数。
  - `souvenir_fragment_count`（整数）：纪念品碎片数量。
  - `minigame_unlocked_flag`（布尔值）：小游戏解锁标志。
  - `daily_play_limit_reached`（布尔值）：每日游玩次数达到上限标志。
- **好感度数据**：
  - `affection_experience`（整数）：好感度经验值。
  - `affection_level`（整数）：好感度等级（0-30）。
  - `experience_to_next_level`（整数）：升级所需经验值。
  - `unlock_content_list`（整数数组）：已解锁内容ID列表。
  - `special_event_trigger_level`（整数）：特殊事件触发等级。
  - `affection_maxed_flag`（布尔值）：好感度满级标志。
  - `reset_affection_flag`（布尔值）：重置好感度标志。
- **剧情数据**：
  - `story_watch_count`（整数）：剧情观看次数。
  - `first_watch_timestamp`（浮点数）：首次观看时间戳。
  - `story_unlocked_flag`（布尔值）：剧情解锁标志。
  - `story_watched_flag`（布尔值）：剧情已观看标志。
  - `story_skip_flag`（布尔值）：剧情跳过标志。
  - `all_stories_unlocked_flag`（布尔值）：所有剧情已解锁标志。
- **纪念品数据**：
  - `souvenir_synthesis_time`（浮点数）：纪念品合成时间。
  - `souvenir_placement_position`（浮点数数组）：纪念品摆放位置（x,y,z）。
  - `souvenir_placement_rotation`（浮点数数组）：纪念品摆放旋转（x,y,z）。
  - `souvenir_synthesized_flag`（布尔值）：纪念品已合成标志。
  - `souvenir_placed_flag`（布尔值）：纪念品已摆放标志。
  - `souvenir_collected_flag`（布尔值）：纪念品已收集标志。
  - `all_souvenirs_unlocked_flag`（布尔值）：所有纪念品已解锁标志。
- **AI行为数据**：
  - `current_behavior_id`（整数）：当前行为ID。
  - `behavior_play_duration`（浮点数）：行为播放时长。
- **拍照模式数据**：
  - `screenshot_count`（整数）：截图数量（仅记录次数，不保存图片）。
- **付费与解锁数据**：
  - `dlc_purchase_timestamp`（浮点数）：DLC购买时间戳。
  - `purchase_platform`（整数）：购买平台（0=iOS，1=Android，2=PC）。
  - `dlc_purchased_flag`（布尔值）：DLC已购买标志。
  - `payment_success_flag`（布尔值）：支付成功标志。
  - `payment_failed_flag`（布尔值）：支付失败标志。
  - `dlc_refunded_flag`（布尔值）：DLC已退款标志。
- **数据联动数据**：
  - `character_unlock_status`（整数数组）：角色解锁状态（0=未拥有，1=已拥有）。
  - `skin_unlock_status`（整数数组）：皮肤解锁状态（0=未拥有，1=已拥有）。
  - `affection_reward_status`（整数数组）：好感度奖励状态（0=未领取，1=已领取）。
  - `story_linkage_status`（整数数组）：剧情联动状态（0=未同步，1=已同步）。

### 核心校验逻辑
- **DLC购买校验**：每次进入宿舍系统前，服务端校验 `dlc_purchased_flag`，防止客户端绕过付费。
- **角色拥有校验**：校验 `character_unlock_status`，确保玩家拥有该角色。
- **互动热点冷却校验**：服务端根据 `cooldown_timer` 校验热点是否处于冷却状态（`hotspot_on_cooldown`），防止客户端篡改冷却时间。
- **好感度经验每日上限校验**：服务端记录每日好感度经验获取总量（`daily_affection_exp_gained`），达到200点后拒绝增加经验。
- **小游戏每日次数校验**：服务端校验 `daily_play_count` 是否超过 `max_daily_play_count`（默认100），防止客户端绕过次数限制。
- **好感度等级解锁校验**：互动动画、小游戏入口、剧情片段等解锁需服务端校验 `affection_level >= required_level`。
- **纪念品合成校验**：服务端校验 `souvenir_fragment_count` 是否满足合成条件。
- **退款处理**：若检测到 `dlc_refunded_flag = true`，回退DLC解锁状态，锁定宿舍系统访问。

## 四、 前后端通信协议 (API & 数据对接)

- **`EnterDormitory`**: C->S / 请求参数: `character_id` (整数) / 返回参数: `dlc_purchased_flag`, `character_ownership_status`, `room_config_data`, `furniture_layout`, `decoration_placement`, `room_state`, `affection_level`, `affection_experience`, `unlock_content_list`, `current_behavior_id`
- **`SaveRoomState`**: C->S / 请求参数: `character_id`, `furniture_layout`, `decoration_placement`, `room_state` / 返回参数: `success` (布尔值)
- **`InteractHotspot`**: C->S / 请求参数: `character_id`, `hotspot_id` / 返回参数: `hotspot_unlocked_flag`, `hotspot_on_cooldown`, `cooldown_timer`, `affection_increment`, `affection_experience`, `affection_level`, `affection_level_up_flag`, `unlock_content_list`, `daily_affection_exp_gained`
- **`StartMinigame`**: C->S / 请求参数: `character_id`, `minigame_id` / 返回参数: `minigame_unlocked_flag`, `daily_play_limit_reached`, `daily_play_count`, `max_daily_play_count`, `minigame_loaded_flag`
- **`EndMinigame`**: C->S / 请求参数: `character_id`, `minigame_id`, `score`, `is_victory` / 返回参数: `reward_experience`, `souvenir_fragment_count`, `affection_experience`, `affection_level`, `daily_play_count`, `daily_play_limit_reached`, `highest_score`, `score_record`
- **`CheckAffectionLevel`**: C->S / 请求参数: `character_id` / 返回参数: `affection_level`, `affection_experience`, `experience_to_next_level`, `affection_maxed_flag`, `daily_affection_exp_gained`
- **`UnlockStory`**: C->S / 请求参数: `character_id`, `story_id` / 返回参数: `story_unlocked_flag`, `story_unlock_affection_level_requirement`, `story_unlock_minigame_achievement_requirement`, `all_stories_unlocked_flag`
- **`WatchStory`**: C->S / 请求参数: `character_id`, `story_id` / 返回参数: `story_watched_flag`, `story_watch_count`, `first_watch_timestamp`, `story_skip_flag`
- **`UnlockSouvenir`**: C->S / 请求参数: `character_id`, `souvenir_id` / 返回参数: `souvenir_synthesized_flag`, `souvenir_fragment_count`, `all_souvenirs_unlocked_flag`
- **`PlaceSouvenir`**: C->S / 请求参数: `character_id`, `souvenir_id`, `souvenir_placement_position`, `souvenir_placement_rotation` / 返回参数: `souvenir_placed_flag`, `success`
- **`SetAIBehavior`**: C->S / 请求参数: `character_id`, `current_behavior_id`, `behavior_play_duration` / 返回参数: `success`
- **`EnterPhotoMode`**: C->S / 请求参数: `character_id` / 返回参数: `photo_mode_active_flag`, `selected_filter_id`, `selected_pose_id`, `selected_expression_id`
- **`TakeScreenshot`**: C->S / 请求参数: `character_id`, `screenshot_count` / 返回参数: `screenshot_taken_flag`, `screenshot_count`
- **`PurchaseDLC`**: C->S / 请求参数: `purchase_platform` / 返回参数: `dlc_purchased_flag`, `payment_success_flag`, `payment_failed_flag`, `dlc_purchase_timestamp`
- **`SyncLinkageData`**: C->S / 请求参数: `character_id` / 返回参数: `character_unlock_status`, `skin_unlock_status`, `affection_reward_status`, `story_linkage_status`, `character_unlocked_flag`, `skin_unlocked_flag`, `affection_reward_claimed_flag`, `story_unlocked_in_main_game_flag`
- **`CheckDailyLimit`**: C->S / 请求参数: `character_id` / 返回参数: `daily_affection_exp_gained`, `daily_play_count`, `daily_play_limit_reached`

## 五、 数值与配置表挂载
程序启动时，读取数值策划提供的 `system_numerical_data.json` 表格，挂载以下配置：
- **房间配置表**：`room_config_data` 定义每个角色ID对应的3D房间场景资源路径。
- **互动热点配置表**：`unlock_affection_level_requirement` 定义每个热点解锁所需好感度等级；`cooldown_timer` 定义热点冷却时间（默认30秒）。
- **小游戏配置表**：`minigame_unlock_affection_level` 定义小游戏解锁所需好感度等级；`max_daily_play_count` 定义每日最大游玩次数（默认100）；`reward_experience` 定义胜利/失败奖励经验值（胜利50点，失败10点）。
- **好感度配置表**：`experience_to_next_level` 定义每级所需经验值（如1级100点，2级200点，递增）；`daily_affection_exp_gained` 每日上限200点。
- **剧情解锁配置表**：`story_unlock_affection_level_requirement` 定义剧情解锁所需好感度等级（如3级、5级、7级）；`story_unlock_minigame_achievement_requirement` 定义小游戏成就要求（如连续3次胜利）。
- **纪念品解锁配置表**：`souvenir_fragment_count` 定义纪念品合成所需碎片数量。
- **AI行为配置表**：`behavior_trigger_probability` 定义各行为触发概率（如看书40%、发呆30%、做家务20%、哼歌10%）；`voice_trigger_probability` 定义语音触发概率（默认0.3）。
- **拍照模式配置表**：`selected_filter_id` 定义滤镜ID（0=清新，1=暖阳，2=复古，3=黑白）；`selected_pose_id` 和 `selected_expression_id` 定义姿势与表情ID。
- **付费配置表**：DLC价格（如$9.99）由商店系统配置，本系统仅读取 `dlc_purchased_flag`。
- **数据联动配置表**：`affection_reward_status` 定义好感度等级奖励（5级解锁头像框，10级解锁名片背景）。

## 六、 开发优先级与依赖链路 (执行排期) ★ 核心

### 阶段一 (P0 - 底层数据与协议)
- **建表**：创建所有持久化数据表（角色房间数据、互动热点数据、小游戏数据、好感度数据、剧情数据、纪念品数据、AI行为数据、拍照模式数据、付费与解锁数据、数据联动数据）。
- **定义API**：实现所有前后端通信接口（`EnterDormitory`, `SaveRoomState`, `InteractHotspot`, `StartMinigame`, `EndMinigame`, `CheckAffectionLevel`, `UnlockStory`, `WatchStory`, `UnlockSouvenir`, `PlaceSouvenir`, `SetAIBehavior`, `EnterPhotoMode`, `TakeScreenshot`, `PurchaseDLC`, `SyncLinkageData`, `CheckDailyLimit`）。
- **后端核心校验逻辑**：
  - 实现DLC购买校验（`dlc_purchased_flag`）。
  - 实现角色拥有校验（`character_unlock_status`）。
  - 实现互动热点冷却校验（`cooldown_timer` 与 `hotspot_on_cooldown`）。
  - 实现好感度经验每日上限校验（`daily_affection_exp_gained` 上限200点）。
  - 实现小游戏每日次数校验（`daily_play_count` 与 `max_daily_play_count`）。
  - 实现好感度等级解锁校验（`affection_level >= required_level`）。
  - 实现纪念品合成校验（`souvenir_fragment_count`）。
  - 实现退款处理（`dlc_refunded_flag` 回退逻辑）。

### 阶段二 (P1 - 前端核心表现)
- **UI框架搭建**：
  - 开发角色选择界面（读取 `character_unlock_status` 显示已解锁角色）。
  - 开发房间主界面（3D场景渲染、视角控制、互动热点高亮）。
  - 开发好感度UI（经验条动画、升级特效、解锁内容提示框）。
  - 开发小游戏界面（规则说明、HUD、结算界面）。
  - 开发剧情播放界面（全屏演出、暂停/快进/跳过）。
  - 开发拍照模式界面（滤镜选择、姿势/表情切换、拍照按钮）。
  - 开发付费弹窗（DLC购买弹窗、支付成功/失败提示）。
  - 开发加载与错误提示（加载中动画、错误弹窗）。
- **接入后端API**：前端所有UI组件对接后端API，实现数据读写。
- **核心玩法跑通**：
  - 角色房间加载与状态管理（`room_state` 流转）。
  - 互动热点点击与动画播放（含冷却逻辑）。
  - 小游戏开始、进行、结束流程（含每日次数与奖励）。
  - 好感度经验增加与等级提升（含每日上限）。
  - 剧情解锁与观看（含好感度等级与小游戏成就条件）。
  - 纪念品解锁与摆放（含碎片合成与位置保存）。
  - AI行为状态机（定时切换、语音触发）。
  - 拍照模式（视角控制、滤镜/姿势/表情切换、截图保存）。
  - DLC购买与解锁流程。
  - 数据联动（角色解锁、皮肤切换、好感度奖励、剧情同步）。

### 阶段三 (P2 - 表现层打磨)
- **特效接入**：
  - 互动热点高亮微光+粒子效果。
  - 好感度升级光效+角色剪影动画。
  - 解锁内容提示框动画。
  - 拍照快门音效。
  - 购买成功解锁特效。
  - 小游戏胜利/失败角色反应动画。
- **边缘异常兜底**：
  - 断线重连：保持房间场景加载，恢复AI行为ID与互动状态，小游戏暂停/恢复，剧情暂停/恢复。
  - 资源缺失：播放默认占位动画（“未找到动画”、“剧情加载失败”、“纪念品”占位模型），记录错误日志。
  - 存储空间不足：截图保存失败提示。
  - 支付中断：断线重连后检查支付结果。
  - 数据损坏：好感度数据重置为1级0经验并提示。
  - 纪念品摆放冲突：自动调整位置或提示。
  - 动画播放期间退出：立即停止动画，不增加经验。
  - 同时点击多个热点：仅处理第一个点击。