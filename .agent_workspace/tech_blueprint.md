# 分析员档案 - 程序开发蓝图

## 一、 整体架构概述

本系统为**弱联网、强客户端渲染**的玩家个人身份展示与社交轻互动模块。核心性能瓶颈在于：
1. **动态背景与3D模型渲染**：需在低端机型降级，避免内存溢出。
2. **毛玻璃/UI透明化效果**：实时高斯模糊对GPU压力大，需提供性能模式开关。
3. **旧系统数据联动**：依赖角色、成就、战斗、好友、通行证5个外部系统API，需设置5秒超时及本地缓存机制。
4. **社交互动**：点赞、留言需服务端校验频率与敏感词，防止刷屏。

技术架构采用 **Client-Server 分离**，前端负责UI渲染、动画播放、本地缓存；后端负责数据持久化、逻辑校验、API网关。

---

## 二、 前端模块划分 (Client)

### 2.1 UI 组件层

| 组件名称 | 功能描述 | 关联模块 |
|---------|--------|---------|
| `ProfileHeader` | 顶部头像、ID、等级、登录天数 | profile_page |
| `SignatureEditor` | 签名输入框（50字符限制+敏感词实时校验） | profile_page |
| `AssistantCharacterSlot` | 助理角色展示区（可拖拽排序，最多6名） | profile_page |
| `AvatarFrameSelector` | 头像框选择面板（已解锁/未解锁状态） | profile_page, economy_monetization |
| `BackgroundSelector` | 背景选择面板（静态/动态，含限时/绝版标签） | profile_page, economy_monetization |
| `CharacterGrid` | 角色收藏馆网格列表（含筛选/排序控件） | collection_showcase |
| `CharacterDetailPanel` | 角色详情页（立绘/模型、属性、皮肤） | collection_showcase |
| `ShowcaseSlot` | 展示柜区域（最多3名，金色边框特效） | collection_showcase |
| `AchievementGrid` | 成就墙网格（已解锁彩色/未解锁灰色） | achievement_wall |
| `AchievementDetailPanel` | 成就详情页（大图、描述、装饰设置） | achievement_wall |
| `FriendListPanel` | 好友列表（在线状态、最近互动排序） | light_social |
| `FriendSearchPanel` | 好友搜索（模糊搜索+结果列表） | light_social |
| `LikeButton` | 点赞按钮（心形图标，已点赞灰色） | light_social |
| `MessageBoard` | 留言板（时间倒序，审核状态显示） | light_social |
| `DynamicBackgroundRenderer` | 动态背景渲染器（粒子效果、动画） | dynamic_background_model_display |
| `CharacterModelViewer` | 3D模型展示器（待机动作、互动反馈） | dynamic_background_model_display |
| `FrostedGlassOverlay` | 毛玻璃/UI透明化层（高斯模糊） | ui_transparency |
| `SharePanel` | 名片生成与分享面板（截图、保存、分享） | profile_page |

### 2.2 表现层控制器

| 控制器名称 | 功能描述 | 对接策划案表现层反馈 |
|-----------|--------|-------------------|
| `ProfileEditController` | 管理编辑模式（头像/背景/签名/助理角色保存） | Toast提示、敏感词变红、加载动画 |
| `CharacterAnimationController` | 控制角色待机动作切换（10-15秒间隔） | 平滑过渡、擦边动作频率限制（30分钟1次） |
| `DynamicBackgroundController` | 加载动态背景（进度条1-3秒） | 加载失败回退静态背景 |
| `ScreenshotController` | 截取当前主页内容生成PNG | 加载动画1-2秒，弹出分享面板 |
| `FriendInteractionController` | 管理点赞、留言发送、好友请求 | 心跳动画、发送中动画、审核通知 |
| `PerformanceModeController` | 低端机型降级（关闭毛玻璃、动态背景降级为静态立绘） | 设置中提供“性能模式”开关 |
| `UITransparencyController` | 管理UI元素透明度（默认30%，点击时临时100%） | 透明度变化平滑，无闪烁 |

---

## 三、 后端逻辑划分 (Server)

### 3.1 持久化数据 (DB)

**核心表：`profile_data`**（玩家档案数据）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| `player_id` | VARCHAR(64) | 主键，玩家唯一ID |
| `avatar_id` | VARCHAR(64) | 当前头像ID，默认'default_avatar' |
| `background_id` | VARCHAR(64) | 当前背景ID，默认'default_bg' |
| `signature_text` | VARCHAR(50) | 签名文本，含敏感词过滤 |
| `assistant_character_ids` | JSON | 助理角色ID列表，最多6个 |
| `showcase_character_ids` | JSON | 展示柜角色ID列表，最多3个 |
| `decorative_medal_ids` | JSON | 装饰徽章ID列表，最多5个 |
| `total_likes_received` | INT | 收到的点赞总数 |
| `profile_visit_count` | INT | 档案主页被访问次数 |

**辅助表：`friend_relation`**（好友关系）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| `player_id` | VARCHAR(64) | 玩家ID |
| `friend_id` | VARCHAR(64) | 好友ID |
| `status` | ENUM('pending','accepted','rejected') | 好友关系状态 |
| `created_at` | DATETIME | 创建时间 |

**辅助表：`like_log`**（点赞日志）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| `id` | BIGINT | 自增主键 |
| `liker_id` | VARCHAR(64) | 点赞者ID |
| `target_id` | VARCHAR(64) | 被点赞者ID |
| `created_at` | DATETIME | 点赞时间 |

**辅助表：`message_board`**（留言板）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| `id` | BIGINT | 自增主键 |
| `sender_id` | VARCHAR(64) | 留言者ID |
| `target_id` | VARCHAR(64) | 留言板所属玩家ID |
| `content` | VARCHAR(100) | 留言内容 |
| `status` | ENUM('pending_review','approved','rejected','deleted') | 审核状态 |
| `created_at` | DATETIME | 留言时间 |

**辅助表：`profile_visit_log`**（访问日志）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| `id` | BIGINT | 自增主键 |
| `visitor_id` | VARCHAR(64) | 访问者ID |
| `target_id` | VARCHAR(64) | 被访问者ID |
| `created_at` | DATETIME | 访问时间 |

**辅助表：`purchase_log`**（付费日志）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| `id` | BIGINT | 自增主键 |
| `player_id` | VARCHAR(64) | 玩家ID |
| `resource_type` | VARCHAR(32) | 资源类型（avatar_frame/background/special_frame） |
| `resource_id` | VARCHAR(64) | 资源ID |
| `amount` | DECIMAL(10,2) | 付费金额 |
| `created_at` | DATETIME | 购买时间 |

### 3.2 核心校验逻辑（必须在服务端执行）

1. **签名敏感词校验**：保存签名时，服务端必须再次校验敏感词（防止客户端绕过）。
2. **头像/背景解锁状态校验**：保存编辑时，校验所选头像/背景是否在已解锁列表中（防止客户端伪造）。
3. **助理角色/展示柜角色拥有校验**：保存时，校验角色ID是否属于玩家已拥有角色列表。
4. **点赞频率限制**：每日对同一好友最多点赞1次，总次数不限（需检查`like_log`当日记录）。
5. **留言敏感词校验**：发送留言时，服务端实时校验敏感词，并设置状态为`pending_review`。
6. **好友请求去重**：检查是否已存在`pending`或`accepted`状态的好友关系。
7. **付费资源解锁校验**：购买时，校验货币余额、限时资源是否过期、通行证等级是否达标。
8. **装饰徽章数量限制**：保存装饰设置时，校验`decorative_medal_ids`长度不超过5。

---

## 四、 前后端通信协议 (API & 数据对接)

### 4.1 核心接口列表

| 接口名 | 方向 | 请求参数 | 返回参数 | 说明 |
|-------|------|---------|---------|------|
| `get_profile_data` | C->S | `player_id` | `profile_data`对象（含所有字段） | 加载档案主页数据 |
| `save_profile_edit` | C->S | `avatar_id, background_id, signature_text, assistant_character_ids` | `{success: bool, error_msg: string}` | 保存档案编辑（服务端校验） |
| `get_character_list` | C->S | `player_id, filter_rarity, filter_element, filter_faction, sort_order` | `character_list`数组 | 获取角色收藏馆列表 |
| `get_character_detail` | C->S | `player_id, character_id` | `character_detail`对象 | 获取角色详情 |
| `update_showcase` | C->S | `player_id, showcase_character_ids` | `{success: bool}` | 更新展示柜角色 |
| `get_achievement_list` | C->S | `player_id, category_filter` | `achievement_list`数组 | 获取成就墙列表 |
| `update_decorative_medals` | C->S | `player_id, decorative_medal_ids` | `{success: bool}` | 更新装饰徽章 |
| `search_friend` | C->S | `keyword` | `player_list`数组 | 模糊搜索好友 |
| `send_friend_request` | C->S | `sender_id, target_id` | `{success: bool, error_msg: string}` | 发送好友请求 |
| `accept_friend_request` | C->S | `player_id, requester_id` | `{success: bool}` | 确认好友请求 |
| `delete_friend` | C->S | `player_id, friend_id` | `{success: bool}` | 删除好友 |
| `like_profile` | C->S | `liker_id, target_id` | `{success: bool, error_msg: string}` | 点赞（服务端校验频率） |
| `send_message` | C->S | `sender_id, target_id, content` | `{success: bool, error_msg: string}` | 发送留言（服务端校验敏感词） |
| `delete_message` | C->S | `player_id, message_id` | `{success: bool}` | 删除留言（校验权限） |
| `get_friend_profile` | C->S | `player_id, friend_id` | `profile_data`对象（只读） | 查看好友档案 |
| `generate_card` | C->S | `player_id` | `{image_url: string}` | 生成名片图片（服务端生成或客户端截图） |
| `purchase_resource` | C->S | `player_id, resource_type, resource_id` | `{success: bool, error_msg: string}` | 购买资源（校验货币、限时、通行证等级） |

### 4.2 数据对接说明

- **旧系统API调用**：后端作为网关，统一调用角色、成就、战斗、好友、通行证系统的内部API，设置5秒超时，缓存结果（缓存有效期30秒）。
- **数据格式**：所有JSON字段使用标准格式，`character_data_cache`、`achievement_data_cache`等缓存对象在客户端本地存储，用于离线展示。

---

## 五、 数值与配置表挂载

### 5.1 配置表读取

程序启动时，读取数值策划提供的 `system_numerical_data.json`，挂载以下配置：

| 配置键 | 类型 | 说明 | 示例值 |
|-------|------|------|-------|
| `signature_max_length` | INT | 签名最大字符数 | 50 |
| `assistant_character_max_count` | INT | 助理角色最大数量 | 6 |
| `showcase_character_max_count` | INT | 展示柜角色最大数量 | 3 |
| `decorative_medal_max_count` | INT | 装饰徽章最大数量 | 5 |
| `message_max_length` | INT | 留言最大字符数 | 100 |
| `daily_like_limit_per_target` | INT | 每日对同一好友点赞上限 | 1 |
| `idle_animation_interval_min` | FLOAT | 待机动作切换最小间隔（秒） | 10.0 |
| `idle_animation_interval_max` | FLOAT | 待机动作切换最大间隔（秒） | 15.0 |
| `special_voice_probability` | FLOAT | 特殊语音触发概率 | 0.1 |
| `risky_action_cooldown` | INT | 擦边动作冷却时间（分钟） | 30 |
| `api_timeout_seconds` | FLOAT | 旧系统API超时时间（秒） | 5.0 |
| `ui_default_opacity` | FLOAT | UI元素默认透明度 | 0.3 |
| `ui_click_opacity` | FLOAT | UI点击时透明度 | 1.0 |
| `ui_opacity_duration` | FLOAT | 透明度变化持续时间（秒） | 0.5 |
| `background_blur_radius` | FLOAT | 背景模糊半径（像素） | 10.0 |
| `free_avatar_frame_ids` | JSON | 免费头像框ID列表 | ["frame_1","frame_2","frame_3","frame_4","frame_5"] |
| `free_background_ids` | JSON | 免费背景ID列表 | ["bg_1","bg_2","bg_3","bg_4","bg_5"] |
| `paid_avatar_frame_prices` | JSON | 付费头像框价格映射 | {"frame_6":6,"frame_7":6} |
| `paid_background_prices` | JSON | 付费背景价格映射 | {"bg_6":30,"bg_7":30} |
| `special_frame_prices` | JSON | 特殊展示框价格映射 | {"sf_1":12,"sf_2":12} |

### 5.2 配置表使用场景

- **前端**：UI组件初始化时读取配置（如签名最大长度、UI透明度）。
- **后端**：校验逻辑中读取配置（如点赞上限、留言长度限制）。
- **性能模式**：低端机型自动读取`background_blur_radius`并设置为0，关闭毛玻璃效果。

---

## 六、 开发优先级与依赖链路 (执行排期)

### 阶段一 (P0 - 底层数据与协议) — 预计2周

| 任务 | 依赖 | 说明 |
|------|------|------|
| 1. 数据库建表 | 无 | 创建`profile_data`、`friend_relation`、`like_log`、`message_board`、`profile_visit_log`、`purchase_log` |
| 2. 定义API接口 | 1 | 完成所有核心API的请求/返回参数定义 |
| 3. 后端核心校验逻辑 | 2 | 实现签名敏感词校验、解锁状态校验、点赞频率限制、留言审核状态机 |
| 4. 旧系统API网关 | 2 | 封装角色、成就、战斗、好友、通行证系统的API调用（含5秒超时和缓存） |
| 5. 配置表加载模块 | 无 | 读取`system_numerical_data.json`并注入全局配置 |

### 阶段二 (P1 - 前端核心表现) — 预计3周

| 任务 | 依赖 | 说明 |
|------|------|------|
| 1. 档案主页UI框架 | 阶段一1,2 | 搭建ProfileHeader、SignatureEditor、AssistantCharacterSlot等组件 |
| 2. 编辑模式逻辑 | 1 | 实现头像/背景选择、签名编辑、助理角色拖拽排序 |
| 3. 角色收藏馆 | 阶段一4 | 实现角色列表、筛选/排序、角色详情页、展示柜 |
| 4. 成就墙 | 阶段一4 | 实现成就列表、详情页、装饰设置 |
| 5. 社交轻互动基础 | 阶段一1,2 | 实现好友列表、搜索、添加/删除、点赞、留言发送 |
| 6. 后端API联调 | 1-5 | 前端接入所有后端API，跑通核心玩法（保存编辑、查看好友档案、点赞、留言） |

### 阶段三 (P2 - 表现层打磨与边缘异常兜底) — 预计2周

| 任务 | 依赖 | 说明 |
|------|------|------|
| 1. 动态背景与3D模型渲染 | 阶段二1 | 实现动态背景加载、角色待机动作切换、互动反馈、擦边动作频率控制 |
| 2. UI透明化/毛玻璃效果 | 阶段二1 | 实现高斯模糊、透明度控制、点击时透明度变化 |
| 3. 名片生成与分享 | 阶段二1 | 实现截图、PNG生成、分享面板（保存到本地、复制链接、跳转外部平台） |
| 4. 性能模式 | 1,2 | 低端机型自动降级（关闭毛玻璃、动态背景降级为静态立绘） |
| 5. 边缘异常兜底 | 阶段二6 | 断线重连、本地缓存展示、API超时处理、数据加载失败提示 |
| 6. 商业化埋点 | 阶段一1,2 | 实现付费解锁流程、限时/绝版资源处理、支付失败回滚 |
| 7. 全链路测试 | 1-6 | 集成测试、压力测试、低端机型兼容性测试 |

### 依赖链路总结

```
阶段一 (P0) → 阶段二 (P1) → 阶段三 (P2)
    ↓              ↓              ↓
 数据库建表      UI框架搭建     动态背景渲染
 API定义        编辑模式逻辑    毛玻璃效果
 后端校验        角色收藏馆     名片生成
 旧系统网关      成就墙         性能模式
 配置表加载      社交互动       边缘异常兜底
                 API联调        商业化埋点
```