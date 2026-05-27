# 账号信息系统 - 程序开发蓝图

## 一、 整体架构概述

本系统为纯客户端展示型系统，核心功能是读取玩家账号数据并渲染个人主页，不涉及强实时同步或高频网络交互。主要性能瓶颈在于3D角色模型加载与渲染，以及大量成就/收集品数据的UI列表化展示。系统需与角色、关卡、基地、好友、聊天等旧系统进行单向数据读取联动，无写入依赖。分享功能需对接外部平台API，存在网络IO开销。

## 二、 前端模块划分 (Client)

### UI 组件层
- **个人主页主界面**：包含头像区、称号区、签名区、背景图区、3D角色展示区、成就墙、图鉴展示区、分享按钮。
- **编辑模式界面**：可编辑的展示元素槽位列表，每个槽位对应一个选择器（头像选择器、称号选择器、签名输入框、背景图选择器、角色选择器、皮肤选择器、动作选择器）。
- **成就墙组件**：网格布局，展示已解锁成就列表，支持精选成就高亮边框。
- **图鉴展示组件**：轮播或卡片布局，展示收集品，精选收集品带动态特效。
- **分享弹窗**：选择分享平台（游戏内聊天、微信、QQ等），生成预览图并调用对应API。
- **奖励解锁提示**：播放特效动画并弹出“解锁新奖励”提示。

### 表现层控制器
- **淡入动画控制器**：进入个人主页时播放淡入动画。
- **3D角色展示控制器**：加载玩家选择的角色模型，根据皮肤切换外观，播放待机动作，支持点击触发特殊互动动作。低端机型自动降级为预渲染2D立绘。
- **特效播放器**：保存成功动画、奖励解锁动画、购买成功动画。
- **实时预览控制器**：编辑模式下，玩家选择新元素后立即更新预览效果。
- **分享截图生成器**：截取当前主页展示角色的高质量立绘或3D渲染图作为分享预览图。

## 三、 后端逻辑划分 (Server)

### 持久化数据 (DB)
- **`player_homepage_config` 表**：记录玩家当前选择的头像ID、称号ID、签名文本、背景图ID、展示角色ID、皮肤ID、动作ID。
- **`player_homepage_featured_achievements` 表**：记录玩家选择的精选成就ID列表（最多6个）。
- **`player_homepage_featured_collections` 表**：记录玩家选择的精选收集品ID列表（最多3个）。
- **`player_unlocked_rewards` 表**：记录玩家已解锁的奖励ID（包括免费和付费）。
- **`player_purchased_rewards` 表**：记录玩家已购买的付费奖励ID。

### 核心校验逻辑
- **所有权校验**：玩家选择的头像、称号、背景、角色、皮肤、动作、成就、收集品必须属于玩家已解锁/拥有的内容。服务端在保存配置时需校验每个ID的合法性。
- **数量限制校验**：精选成就最多6个，精选收集品最多3个，签名文本最多50字符。
- **重复购买校验**：玩家尝试购买已解锁的付费内容时，服务端阻止并返回“已拥有”。
- **货币校验**：购买付费内容时，校验玩家货币是否充足，不足则返回错误。
- **交易回滚**：购买失败（网络异常等）时，服务端回滚交易并返回错误。
- **奖励发放校验**：成就/收集里程碑达成时，校验玩家背包是否满，满则暂存邮件。
- **内容审核校验**：所有展示内容需通过内容审核，违规内容立即下架。

## 四、 前后端通信协议 (API & 数据对接)

- **`GetHomepageConfig`**: C->S / 请求参数: 无 / 返回参数: `player_homepage_config` 对象（包含头像ID、称号ID、签名文本、背景图ID、展示角色ID、皮肤ID、动作ID）。
- **`SaveHomepageConfig`**: C->S / 请求参数: `player_homepage_config` 对象 / 返回参数: 成功/失败状态码。
- **`GetFeaturedAchievements`**: C->S / 请求参数: 无 / 返回参数: 精选成就ID列表（最多6个）。
- **`SetFeaturedAchievements`**: C->S / 请求参数: 成就ID列表（最多6个）/ 返回参数: 成功/失败状态码。
- **`GetFeaturedCollections`**: C->S / 请求参数: 无 / 返回参数: 精选收集品ID列表（最多3个）。
- **`SetFeaturedCollections`**: C->S / 请求参数: 收集品ID列表（最多3个）/ 返回参数: 成功/失败状态码。
- **`GetUnlockedRewards`**: C->S / 请求参数: 无 / 返回参数: 已解锁奖励ID列表。
- **`PurchaseReward`**: C->S / 请求参数: 奖励ID / 返回参数: 成功/失败状态码，失败原因（货币不足/已拥有/网络异常）。
- **`ClaimAchievementReward`**: C->S / 请求参数: 成就ID / 返回参数: 成功/失败状态码，失败原因（背包满/数据错误）。
- **`GetPlayerStatistics`**: C->S / 请求参数: 无 / 返回参数: `player_statistics` 对象（包含主线最高章节、深渊最高层数、角色收集度等）。
- **`GetAchievementList`**: C->S / 请求参数: 无 / 返回参数: 成就列表（每个成就包含ID、名称、描述、进度、是否解锁等）。
- **`GetCollectionProgress`**: C->S / 请求参数: 无 / 返回参数: 收集图鉴进度数据（包含总完成度、各分类进度等）。
- **`ShareHomepage`**: C->S / 请求参数: 分享平台列表 / 返回参数: 分享链接或二维码资源路径。
- **`GetLegacyData`**: C->S / 请求参数: 数据类型（角色/武器/关卡/基地/好友/聊天）/ 返回参数: 对应旧系统的数据对象。

## 五、 数值与配置表挂载

程序启动时，读取数值策划提供的 `system_numerical_data.json` 表格，并挂载到全局配置管理器中。具体挂载方式如下：

1. **配置表数据结构映射**：将 JSON 中的 `field_dictionary` 字段映射为程序内的配置表对象。每个字段的 `type` 和 `range` 用于运行时数据校验。例如：
   - `player_level`: 类型为整数，取值范围 1-100，默认值 1。
   - `signature_text`: 类型为字符串，最大长度 50 字符，默认值空字符串。
   - `id_ranges`: 从 `field_dictionary` 中提取所有 ID 类型字段的取值范围，用于校验玩家选择的 ID 是否合法。具体包括：
     - `avatar_id`: 1-9999
     - `title_id`: 1-9999
     - `background_id`: 1-9999
     - `avatar_frame_id`: 1-9999
     - `display_character_id`: 1-9999
     - `skin_id`: 1-9999
     - `action_id`: 1-9999
     - `effect_title_id`: 1-9999（特效称号ID范围，用于校验特效称号的合法性）

2. **枚举值映射**：将 `relations_and_enums` 中的 `状态码枚举` 映射为程序内的枚举类型，用于限制字段的可选值。例如：
   - `achievement_category`: 枚举值包括“战斗”、“收集”、“社交”、“探索”、“活动”。
   - `collection_category`: 枚举值包括“角色”、“武器”、“皮肤”、“家具”、“其他”。
   - `share_content_type`: 枚举值包括“link”、“image”、“card”。
   - `share_platform_list`: 枚举值包括“game_chat”、“wechat”、“qq”、“weibo”。

3. **默认值加载**：当玩家首次进入个人主页或数据缺失时，系统自动加载 `field_dictionary` 中定义的默认值。例如：
   - 默认头像ID为1。
   - 默认背景图ID为1。
   - 默认展示角色ID为1。
   - 默认签名文本为空字符串。

4. **配置热更新**：支持在游戏运行期间重新加载 `system_numerical_data.json`，以应对数值调整。更新后需重新校验所有已加载的配置数据。

## 六、 开发优先级与依赖链路 (执行排期) ★ 核心

### 阶段一 (P0 - 底层数据与协议)
- **建表**：创建 `player_homepage_config`、`player_homepage_featured_achievements`、`player_homepage_featured_collections`、`player_unlocked_rewards`、`player_purchased_rewards` 表。
- **定义 API**：定义所有前后端通信接口（GetHomepageConfig、SaveHomepageConfig、GetFeaturedAchievements、SetFeaturedAchievements、GetFeaturedCollections、SetFeaturedCollections、GetUnlockedRewards、PurchaseReward、ClaimAchievementReward、GetPlayerStatistics、GetAchievementList、GetCollectionProgress、ShareHomepage、GetLegacyData）。
- **后端核心校验逻辑**：实现所有权校验、数量限制校验、重复购买校验、货币校验、交易回滚、奖励发放校验、内容审核校验。
- **配置表加载**：实现 `system_numerical_data.json` 的读取、映射、默认值加载和热更新机制。

### 阶段二 (P1 - 前端核心表现)
- **UI 框架搭建**：开发个人主页主界面、编辑模式界面、成就墙组件、图鉴展示组件、分享弹窗、奖励解锁提示。
- **接入后端 API**：前端调用所有后端接口，实现数据加载、保存、购买、分享等核心流程。
- **核心玩法跑通**：实现编辑模式下的实时预览、保存成功动画、成就/收集品展示、分享功能。
- **3D角色展示控制器**：实现角色模型加载、皮肤切换、待机动作播放、点击互动。低端机型降级为2D立绘。
- **表现层控制器**：实现淡入动画、特效播放器、分享截图生成器。

### 阶段三 (P2 - 表现层打磨)
- **特效接入**：为奖励解锁、购买成功、保存成功等事件添加更丰富的特效动画。
- **边缘异常兜底**：实现数据损坏/缺失时加载默认模板、网络异常时提示重试、低端机型自动降级、分享失败时提示、重复购买阻止、背包满时暂存邮件、内容审核下架等所有边界情况。
- **性能优化**：优化3D角色渲染性能，优化成就/收集品列表的UI虚拟化滚动，减少内存占用。
- **外部平台对接**：完成微信、QQ等外部平台分享API的对接与测试。