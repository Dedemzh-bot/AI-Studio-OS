# 程序开发蓝图 (Tech Blueprint) - 【角色私人宿舍】系统

## 一、 整体架构概述

【角色私人宿舍】系统是一个**强客户端表现、弱实时交互**的模块。核心性能瓶颈在于**客户端渲染**（角色模型高面数、Jiggle Physics、动态光影）和**资源加载**（场景预加载与缓存）。服务端主要负责**数据持久化**（每日次数、好感度经验、解锁状态）和**防作弊校验**（每日次数上限、购买状态验证）。前后端通信采用**请求-响应**模式，无长连接需求。

## 二、 前端模块划分 (Client)

### UI 组件层
- **入口组件**：主界面“宿舍”按钮（状态：locked/unlocked/entered）。
- **角色选择界面**：展示已拥有角色列表，每个角色项显示头像、名字、好感度等级。
- **房间主场景**：
  - 极简操作UI（返回、对话、姿势切换、设置按钮）。
  - 好感度进度条（顶部居中）。
  - 触摸反馈提示（粉色心形图标）。
  - 姿势选择轮盘。
  - 每日次数提示（灰色文字）。
- **购买弹窗**：核心模块购买确认弹窗、家具礼包购买弹窗。
- **庆祝动画**：解锁成功全屏庆祝动画。

### 表现层控制器
- **运镜控制器**：管理进入房间时的专属运镜动画（脚部到面部），支持玩家点击中断。
- **触摸反馈控制器**：
  - 检测触摸点是否落在预定义碰撞体（`Touch_Feedback_Map.md`）。
  - 并行播放语音、表情动画、动作动画、Jiggle Physics。
  - 管理“骚扰”判定（每秒超过3次）。
  - 管理“害羞”状态（敏感区域触摸后泛红）。
- **姿势切换控制器**：管理角色姿势过渡动画（站立→坐姿→躺卧）。
- **服装联动控制器**：查询 `Skin_SpecialTouch_Config.json`，覆盖通用触摸反馈。
- **UI极简化控制器**：管理按钮淡入淡出（无操作3秒后淡出，触摸恢复）。
- **性能降级管理器**：根据设备性能自动切换动态/静态光影、Jiggle Physics帧率、模型LOD。

## 三、 后端逻辑划分 (Server)

### 持久化数据 (DB)
- **`PlayerDormitoryData`**（主表，以 `playerId` 为键）：
  - `isUnlocked` (bool)：是否已购买解锁。
  - `roomData` (map<string, RoomData>)：以 `roleId` 为键的每个角色的房间数据。
    - `affectionLevel` (int)：好感度等级（1-15）。
    - `affectionExp` (int)：好感度经验值（0-52500）。
    - `dailyInteractionCount` (int)：今日有效触摸次数（0-50）。
    - `dailyDialogueCount` (int)：今日有效对话次数（0-5）。
    - `currentPoseId` (string)：当前姿势ID。
    - `currentFurnitureSetId` (string)：当前家具套装ID。
    - `unlockedFurnitureSets` (array<string>)：已解锁家具套装列表。
    - `unlockedDialogues` (array<string>)：已解锁对话ID列表。
    - `unlockedPoses` (array<string>)：已解锁姿势ID列表。
- **`PurchaseLog`**（关联表）：记录玩家购买记录（商品ID、购买时间）。

### 核心校验逻辑
- **购买校验**：
  - 校验 `purchase_log` 中是否已存在 `shop_item_dormitory_unlock`，防止重复购买。
  - 校验玩家货币是否充足（`player_cash`）。
- **每日次数校验**：
  - 每次触摸请求时，校验 `dailyInteractionCount < 50`。
  - 每次对话请求时，校验 `dailyDialogueCount < 5`。
  - 每日00:00定时任务原子性重置所有玩家的 `dailyInteractionCount` 和 `dailyDialogueCount`。
- **好感度升级校验**：
  - 每次增加经验后，校验 `affectionExp` 是否达到下一等级所需经验（参照好感度等级解锁映射表）。
  - 若达到，更新 `affectionLevel`，并解锁对应内容（对话、姿势、家具）。
- **断线重连校验**：
  - 玩家登录时，校验订单状态。若支付成功但 `isUnlocked` 为 false，补写数据并触发解锁提示。
  - 新角色入队时，自动初始化 `roomData[roleId]`。

## 四、 前后端通信协议 (API & 数据对接)

### 核心接口

1. **`GetPlayerDormitoryData`**: C->S / 请求参数: `playerId` / 返回参数: `PlayerDormitoryData` 对象。
2. **`PurchaseDormitoryCorePack`**: C->S / 请求参数: `playerId` / 返回参数: `{ success: bool, errorCode: string }`。
   - 服务端校验：货币充足、未购买过。
   - 成功后：`isUnlocked = true`，初始化所有已拥有角色的 `roomData`。
3. **`PurchaseFurniturePack`**: C->S / 请求参数: `playerId`, `furniturePackId` / 返回参数: `{ success: bool, errorCode: string }`。
   - 服务端校验：货币充足、未购买过该礼包。
   - 成功后：将 `furniturePackId` 添加到所有已拥有角色的 `unlockedFurnitureSets`。
4. **`EnterRoom`**: C->S / 请求参数: `playerId`, `roleId` / 返回参数: `RoomData`（该角色的房间数据）。
5. **`RecordDailyInteraction`**: C->S / 请求参数: `playerId`, `roleId`, `touchAreaId` / 返回参数: `{ success: bool, newInteractionCount: int, newAffectionExp: int, levelUp: bool, newLevel: int }`。
   - 服务端校验：`dailyInteractionCount < 50`。
   - 成功后：`dailyInteractionCount += 1`，`affectionExp += 10`。
6. **`RecordDailyDialogue`**: C->S / 请求参数: `playerId`, `roleId`, `dialogueId` / 返回参数: `{ success: bool, newDialogueCount: int, newAffectionExp: int, levelUp: bool, newLevel: int }`。
   - 服务端校验：`dailyDialogueCount < 5`。
   - 成功后：`dailyDialogueCount += 1`，`affectionExp += 50`。
7. **`UpdateRoomCustomization`**: C->S / 请求参数: `playerId`, `roleId`, `furnitureSetId` / 返回参数: `{ success: bool }`。
   - 服务端校验：`furnitureSetId` 是否在 `unlockedFurnitureSets` 中。
8. **`SwitchPose`**: C->S / 请求参数: `playerId`, `roleId`, `newPoseId` / 返回参数: `{ success: bool }`。
   - 服务端校验：`newPoseId` 是否在 `unlockedPoses` 中。
9. **`GetAffectionLevel`**: S->C（被动调用）/ 用于前端UI显示好感度等级。
10. **`AddAffectionExp`**: S->C（被动调用）/ 用于全局好感度系统同步经验值。

## 五、 数值与配置表挂载

程序启动时，需加载以下配置表（JSON格式），并缓存到内存中：

### 5.1 `Affection_Level_Config.json`（好感度等级解锁映射表）
- **来源**：系统策划案 6.1 节。
- **结构**：
  ```json
  [
    {
      "level": 1,
      "requiredExp": 0,
      "unlockDialogues": [],
      "unlockPoses": ["pose_stand"],
      "unlockFurnitureSets": ["furniture_default"]
    },
    {
      "level": 2,
      "requiredExp": 500,
      "unlockDialogues": ["dialogue_01"],
      "unlockPoses": [],
      "unlockFurnitureSets": []
    },
    // ... 直至 level 15
  ]
  ```
- **挂载点**：`AffectionGrowthSystem` 模块，用于校验升级和解锁内容。

### 5.2 `Touch_Feedback_Map.json`（触摸反馈映射表）
- **来源**：系统策划案 6.2 节 + `Touch_Feedback_Map.md`。
- **结构**：
  ```json
  [
    {
      "touchRegionId": "touch_head",
      "regionName": "头部",
      "voiceId": "voice_head_01",
      "expressionId": "expr_happy",
      "actionId": "action_head_tilt",
      "jigglePhysicsStrength": 0,
      "isSensitive": false
    },
    // ... 其他区域
  ]
  ```
- **挂载点**：`TouchFeedbackController` 模块，用于查询反馈组合。

### 5.3 `Daily_Limit_Config.json`（每日次数上限配置表）
- **来源**：系统策划案 6.3 节。
- **结构**：
  ```json
  {
    "maxDailyInteraction": 50,
    "maxDailyDialogue": 5,
    "resetTime": "00:00",
    "interactionExpPerTouch": 10,
    "dialogueExpPerCompletion": 50,
    "maxDailyExp": 750
  }
  ```
- **挂载点**：`DailyResetSystem` 和 `InteractionValidator` 模块。

### 5.4 `Skin_SpecialTouch_Config.json`（皮肤专属触摸反馈配置）
- **来源**：系统策划案 3.4 节。
- **结构**：
  ```json
  {
    "skin_swimsuit_01": {
      "touch_chest": {
        "voiceId": "voice_chest_swimsuit_01",
        "expressionId": "expr_blush_deep",
        "jigglePhysicsStrength": 3
      }
    },
    "skin_maid_01": {
      "touch_hand": {
        "voiceId": "voice_hand_maid_01",
        "actionId": "action_skirt_lift"
      }
    }
  }
  ```
- **挂载点**：`CostumeLinkageController` 模块，用于覆盖通用反馈。

### 5.5 `Item_Definition_Table.json`（商品定义表）
- **来源**：系统策划案 4.1 节 + 数值策划文档中的定价信息。
- **结构**：
  ```json
  [
    {
      "itemId": "shop_item_dormitory_unlock",
      "itemName": "私人宿舍核心模块",
      "price": 30,
      "currencyType": "cash",
      "itemType": "core_module"
    },
    {
      "itemId": "shop_item_furniture_pack_01",
      "itemName": "和风家具礼包",
      "price": 12,
      "currencyType": "cash",
      "itemType": "furniture_pack",
      "furnitureSetId": "furniture_japanese"
    },
    {
      "itemId": "shop_item_furniture_pack_02",
      "itemName": "现代简约家具礼包",
      "price": 12,
      "currencyType": "cash",
      "itemType": "furniture_pack",
      "furnitureSetId": "furniture_modern"
    }
  ]
  ```
- **挂载点**：`ShopSystem` 模块，用于商品展示和购买校验。**注意**：`price` 字段的值来源于系统策划案 4.1 节中的定价说明（¥30 / $4.99 等），数值策划文档中未提供独立的商品定价表，因此本表作为程序开发时的定价数据源。若后续数值策划提供正式定价表，需以此为准进行替换。

### 5.6 `Pose_Config.json`（姿势配置表）
- **来源**：系统策划案 3.3 节。
- **结构**：
  ```json
  [
    {
      "poseId": "pose_stand",
      "poseName": "站立",
      "unlockLevel": 1,
      "cameraPosition": [0, 1.5, 1.5],
      "cameraRotation": [0, 0, 0]
    },
    {
      "poseId": "pose_sit_bed",
      "poseName": "坐在床边",
      "unlockLevel": 5,
      "cameraPosition": [0, 1.0, 1.2],
      "cameraRotation": [0, 0, 0]
    },
    {
      "poseId": "pose_lie_bed",
      "poseName": "慵懒躺卧",
      "unlockLevel": 10,
      "cameraPosition": [0, 0.5, 1.0],
      "cameraRotation": [0, 0, 0]
    },
    {
      "poseId": "pose_cuddle",
      "poseName": "依偎",
      "unlockLevel": 15,
      "cameraPosition": [0, 1.2, 1.0],
      "cameraRotation": [0, 0, 0]
    }
  ]
  ```
- **挂载点**：`PoseSwitchController` 模块，用于姿势解锁判断和摄像机定位。

## 六、 开发优先级与依赖链路 (执行排期) ★ 核心

### 阶段一 (P0 - 底层数据与协议)
- **建表**：创建 `PlayerDormitoryData` 数据库表，包含所有字段。
- **定义 API**：完成所有核心接口（1-8）的 protobuf 定义和桩代码。
- **后端核心校验逻辑**：
  - 购买校验（`PurchaseDormitoryCorePack`、`PurchaseFurniturePack`）。
  - 每日次数校验（`RecordDailyInteraction`、`RecordDailyDialogue`）。
  - 好感度升级校验（`AddAffectionExp` 后的等级检查）。
  - 每日重置定时任务（原子性重置所有玩家的每日次数）。
- **配置表加载**：实现 `Affection_Level_Config.json`、`Daily_Limit_Config.json`、`Item_Definition_Table.json` 的加载和缓存。
- **依赖**：无（纯后端逻辑，可独立开发）。

### 阶段二 (P1 - 前端核心表现)
- **UI 框架搭建**：
  - 入口组件、角色选择界面、房间主场景 UI 框架。
  - 购买弹窗、庆祝动画。
- **接入后端 API**：
  - 实现 `GetPlayerDormitoryData`、`EnterRoom` 的客户端调用。
  - 实现 `RecordDailyInteraction`、`RecordDailyDialogue` 的客户端调用。
- **核心玩法跑通**：
  - 运镜控制器（进入房间动画）。
  - 触摸反馈控制器（基础触摸检测、语音/表情/动作播放）。
  - 好感度进度条 UI 更新。
  - 姿势切换控制器（基础切换逻辑）。
- **依赖**：阶段一完成后联调。

### 阶段三 (P2 - 表现层打磨)
- **特效接入**：
  - Jiggle Physics 系统集成。
  - 触摸反馈提示（粉色心形图标）。
  - “害羞”状态（面部泛红、眼神迷离）。
  - “骚扰”判定与反馈（红色感叹号、警告音效）。
- **边缘异常兜底**：
  - 断线重连逻辑（登录时校验订单状态、补写数据）。
  - 新角色入队时自动初始化 `roomData`。
  - 性能降级策略（动态光影→静态光影、Jiggle Physics 降帧、模型 LOD 切换）。
  - 资源缺失降级（皮肤专属配置缺失时使用通用反馈）。
- **皮肤联动**：
  - 加载 `Skin_SpecialTouch_Config.json`，实现皮肤专属触摸反馈覆盖。
- **家具系统**：
  - 实现 `UpdateRoomCustomization` 接口。
  - 房间装修界面（家具套装切换）。
- **数据埋点**：实现所有关键事件埋点（`dormitory_enter`、`dormitory_touch` 等）。
- **依赖**：阶段二完成后进行。