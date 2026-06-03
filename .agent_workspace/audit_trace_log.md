
--- 审查时间: 2026-06-03 17:08:16 ---
### Issue 1 [严重级别: 致命]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、 前后端通信协议 (API & 数据对接) - 4.1 核心接口
- 问题描述: 系统策划案中明确描述了【方案保存与切换】功能（2.8节），其中包含【方案删除】操作。程序蓝图虽然定义了 `Dormitory_DeleteScheme` 接口，但缺少【方案列表查询】接口。玩家进入方案切换界面时，需要拉取已保存的方案列表（含缩略图、名称等），但当前API列表中没有提供该接口。这会导致方案切换界面无法展示已有方案，功能断链。
- 修改建议: 请Tech Architect在核心接口列表中补充一个用于查询玩家所有已保存方案列表的接口（例如 `Dormitory_GetSchemeList`），并定义其请求与返回参数，确保前端能获取到方案ID、名称、缩略图等必要信息。
### Issue 2 [严重级别: 高]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、 前后端通信协议 (API & 数据对接) - 4.1 核心接口
- 问题描述: 系统策划案中【场景布置】功能（2.5节）和【场景模板切换】功能（2.6节）都涉及家具数据的保存与更新。程序蓝图定义了 `Dormitory_SaveFurniture` 和 `Dormitory_SwitchTemplate` 接口，但缺少一个【获取当前场景家具数据】的接口。当玩家重新进入宿舍或从方案切换回来时，客户端需要从服务端拉取当前 `scene_furniture_data` 来渲染场景，否则场景中的家具将无法正确显示。
- 修改建议: 请Tech Architect补充一个用于获取当前角色宿舍完整配置数据的接口（例如 `Dormitory_GetConfig`），该接口应返回 `character_dormitory_config` 对象，包含场景模板ID、家具数据、装扮ID、姿势ID、表情ID等所有必要信息。
### Issue 3 [严重级别: 高]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 三、 后端逻辑划分 (Server) - 3.2 核心校验逻辑
- 问题描述: 系统策划案中【方案保存与切换】功能（2.8节）提到，方案保存时需自动截取场景缩略图，用于方案列表展示。程序蓝图在方案管理器（2.2节）中提到了“自动截取缩略图”，但在后端校验逻辑（3.2节）和API定义（4.1节）中，均未提及缩略图的生成、存储与传输机制。缩略图是方案列表展示的核心数据，缺少该机制会导致方案切换界面无法展示预览图，严重影响用户体验。
- 修改建议: 请Tech Architect在方案保存接口（`Dormitory_SaveScheme`）的请求或返回参数中，明确缩略图的处理方式。建议方案：由客户端在保存时上传缩略图（Base64或文件），服务端存储缩略图URL或二进制数据，并在方案列表查询接口中返回该URL。
### Issue 4 [严重级别: 中]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、 前后端通信协议 (API & 数据对接) - 4.1 核心接口
- 问题描述: 系统策划案中【拍照模式】功能（2.7节）提到，截图保存至本地相册，文件名为 `[CHARACTER_NAME]_[TIMESTAMP].png`。程序蓝图在拍照模式控制器（2.2节）中也提到了文件名格式。但系统策划案中角色名称是动态的（不同角色名称不同），而数值说明书中的 `character_id` 是字符串类型。程序蓝图和API定义中均未明确客户端如何获取当前角色的显示名称（`CHARACTER_NAME`）来生成文件名。这可能导致文件名生成逻辑缺失或硬编码。
- 修改建议: 请Tech Architect在角色选择接口或宿舍加载接口的返回数据中，增加一个字段用于返回当前角色的显示名称（例如 `character_name`），供客户端在拍照时生成文件名使用。
### Issue 5 [严重级别: 中]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 三、 后端逻辑划分 (Server) - 3.2 核心校验逻辑
- 问题描述: 系统策划案中【场景模板切换】功能（2.6节）提到，切换后原场景中的家具/装饰品自动适配新模板，若新模板有对应位置则保留，否则自动回收至背包。程序蓝图在 `Dormitory_SwitchTemplate` 接口的返回参数中包含了 `removed_furniture_ids`，但缺少一个【家具适配映射表】或【适配逻辑】的定义。服务端如何判断哪些家具可以适配到新模板？哪些需要回收？当前文档中没有提供任何适配规则或配置表，这会导致该功能无法实现或实现错误。
- 修改建议: 请Tech Architect与System Planner和Numerical Planner协作，定义一套家具适配规则。例如：每个场景模板可以定义一个“可适配家具白名单”，或者定义家具的“适配标签”（如“室内”、“户外”），服务端根据新模板的标签进行匹配。同时，需要在配置表中补充相应的适配映射数据。
**当前审查总计问题:** 5 个

--- 审查时间: 2026-06-03 17:10:44 ---
### Issue 1 [严重级别: 致命]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、 前后端通信协议 (API & 数据对接)
- 问题描述: 蓝图中的 `Dormitory_SwitchTemplate` API 返回参数中包含了 `removed_furniture_ids`，并在后端校验逻辑中引用了 `system_numerical_data.json` 中未定义的 `scene_template_furniture_adapter_map` 配置表。该配置表在系统策划案和数值配表中均不存在，导致后端逻辑无法实现，属于未定义级致命断链。
- 修改建议: 请 Tech Architect 移除对 `scene_template_furniture_adapter_map` 的引用，并重新定义场景模板切换时家具适配的规则（例如：切换模板时，所有家具自动回收至背包，或由客户端根据固定规则处理）。同时，更新 `Dormitory_SwitchTemplate` API 的返回参数，移除 `removed_furniture_ids`。
### Issue 2 [严重级别: 高]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、 前后端通信协议 (API & 数据对接)
- 问题描述: 系统策划案中描述了“方案保存时自动截取场景缩略图”，但蓝图中的 `Dormitory_SaveScheme` API 的请求参数中并未包含缩略图数据（如 base64 编码的图片）。同时，蓝图中的方案列表展示也依赖此缩略图，缺少该字段将导致方案管理功能无法正常实现。
- 修改建议: 请 Tech Architect 在 `Dormitory_SaveScheme` 的请求参数中增加一个可选字段（如 `thumbnail`），用于上传缩略图数据。同时，在 `Dormitory_LoadScheme` 或 `Dormitory_GetOwnedItems` 的返回参数中，为每个方案增加缩略图字段。
### Issue 3 [严重级别: 高]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 三、 后端逻辑划分 (Server) - 核心校验逻辑
- 问题描述: 系统策划案中明确提到“若玩家在切换方案时未保存当前状态，系统自动保存当前状态为临时方案（不占用槽位）”。但蓝图中的后端逻辑和 API 接口均未定义任何与“临时方案”相关的存储、读取或清理逻辑。这会导致玩家数据丢失或状态不一致。
- 修改建议: 请 Tech Architect 在 `player_character_dormitory` 表中增加一个字段（如 `temp_scheme_data`）用于存储临时方案，并定义其生命周期（如：在保存新方案或加载正式方案时被覆盖）。同时，在 `Dormitory_LoadScheme` 或相关接口中，增加对临时方案的自动保存逻辑。
### Issue 4 [严重级别: 高]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、 前后端通信协议 (API & 数据对接)
- 问题描述: 系统策划案中描述了“拍照模式”下可以“微调角色位置、朝向”，但蓝图中的 API 接口列表并未提供任何用于更新角色位置或朝向的接口。`Dormitory_SavePose` 和 `Dormitory_SaveExpression` 仅处理姿势和表情ID，无法处理空间坐标数据。这导致拍照模式的核心功能无法实现。
- 修改建议: 请 Tech Architect 新增一个 API（如 `Dormitory_SaveCharacterTransform`），用于保存角色在场景中的位置和朝向数据。或者在现有的 `Dormitory_SaveFurniture` 或 `Dormitory_SaveScheme` 接口中，增加角色变换数据的字段。
### Issue 5 [严重级别: 中]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 三、 后端逻辑划分 (Server) - 核心校验逻辑
- 问题描述: 系统策划案中“场景模板切换”的流转逻辑提到“若玩家在切换模板时未保存当前布置，系统自动保存当前布置后再切换”。但蓝图中的 `Dormitory_SwitchTemplate` API 逻辑并未包含此自动保存步骤。这会导致玩家在未保存的情况下切换模板，丢失布置数据。
- 修改建议: 请 Tech Architect 在 `Dormitory_SwitchTemplate` 的后端逻辑中，增加一个前置步骤：在切换模板前，自动将当前的 `scene_furniture_data` 保存到临时方案或直接更新到 `character_dormitory_config` 中。
**当前审查总计问题:** 5 个

--- 审查时间: 2026-06-03 17:12:34 ---
### Issue 1 [严重级别: 致命]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、前后端通信协议 (API & 数据对接)
- 问题描述: API接口列表中缺少 `Dormitory_GetUnlockStatus` 接口的定义，但后端逻辑中明确提到了需要校验姿势/表情/场景模板/家具的解锁状态，且前端需要展示未解锁项的锁图标与解锁条件。该接口是核心校验逻辑的前置依赖，缺失将导致解锁状态无法获取，阻塞所有付费内容的展示与校验。
- 修改建议: 在API接口列表中补充 `Dormitory_GetUnlockStatus` 接口的完整定义，包括请求参数、返回参数及状态码枚举。
### Issue 2 [严重级别: 致命]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、前后端通信协议 (API & 数据对接)
- 问题描述: API接口 `Dormitory_SaveFurniture` 的返回参数仅使用了 `furniture_placement_status` 枚举，但该枚举中包含了“位置重叠”、“超出边界”、“数量上限”等错误状态。然而，系统策划案中明确要求“若玩家在布置模式下断线，所有未保存的布置操作丢失”，但API接口中没有任何关于断线重连后数据同步或冲突处理的机制定义。这会导致断线后客户端本地状态与服务端状态不一致，产生数据丢失或覆盖的严重问题。
- 修改建议: 在 `Dormitory_SaveFurniture` 接口中增加版本号或时间戳字段，用于断线重连后的冲突检测与合并逻辑。或者在API描述中明确说明断线重连后的数据同步策略（例如：以服务端最后一次保存的数据为准，客户端本地未保存的修改丢弃）。
### Issue 3 [严重级别: 高]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 三、后端逻辑划分 (Server) - 核心校验逻辑
- 问题描述: 后端校验逻辑中提到了“方案保存校验：服务端校验方案名称长度不超过 `[SCHEME_NAME_MAX_LENGTH]`，方案槽位数量不超过已解锁槽位数（初始 `[FREE_SCHEME_SLOT_COUNT]`），并检查方案名称是否重复”。但是，系统策划案中明确提到“免费提供 `[FREE_SCHEME_SLOT_COUNT]` 个方案槽位，超出需付费解锁”，而数值配表中仅定义了 `free_scheme_slot_count` 为3，没有提供付费解锁槽位的相关字段（如付费槽位价格、最大槽位总数等）。这导致“付费解锁”这一商业化逻辑在数值层面完全缺失，无法实现。
- 修改建议: 在数值配表中补充付费方案槽位的相关字段，例如 `paid_scheme_slot_price`（价格）、`max_scheme_slot_count`（最大槽位总数），并在后端校验逻辑中引用这些字段。
### Issue 4 [严重级别: 高]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、前后端通信协议 (API & 数据对接)
- 问题描述: API接口 `Dormitory_SaveScheme` 的请求参数中包含 `thumbnail_base64`（方案保存时自动截取的场景缩略图base64编码）。但是，系统策划案中并未定义缩略图的生成时机、存储方式、大小限制或压缩格式。将base64编码的缩略图直接通过API传输会给服务端带来巨大的存储压力和网络带宽消耗，且没有明确的存储策略（是存为文件还是数据库字段？）。这是一个未定义的技术实现细节，可能导致性能瓶颈或存储溢出。
- 修改建议: 在技术蓝图中明确缩略图的生成与存储策略：例如，缩略图由客户端生成并压缩后上传，服务端存储为文件并返回URL；或者缩略图由服务端根据方案数据动态渲染生成。同时，定义缩略图的最大尺寸（如256x256）和文件大小限制。
### Issue 5 [严重级别: 中]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、前后端通信协议 (API & 数据对接)
- 问题描述: 系统策划案中明确提到“若玩家在切换方案时未保存当前状态，系统自动保存当前状态为临时方案（不占用槽位）”。但是，API接口列表中没有任何与“临时方案”相关的接口定义（如 `Dormitory_SaveTemporaryScheme` 或 `Dormitory_LoadTemporaryScheme`）。临时方案的存储、加载、生命周期管理在技术蓝图中完全缺失，导致该功能无法实现。
- 修改建议: 在API接口列表中补充临时方案的相关接口，例如 `Dormitory_SaveTemporaryScheme`（保存临时方案，不占用槽位）和 `Dormitory_LoadTemporaryScheme`（加载临时方案），并明确临时方案的存储位置（如客户端本地缓存或服务端临时存储）和生命周期（如退出宿舍时自动删除）。
**当前审查总计问题:** 5 个

--- 审查时间: 2026-06-03 17:14:49 ---
### Issue 1 [严重级别: 致命]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 三、 后端逻辑划分 (Server) -> 持久化数据 (DB)
- 问题描述: 后端持久化数据表中缺少 `player_id` 字段定义。系统策划案明确说明数据以 `player_id + character_id` 为复合主键，数值说明书也定义了 `player_id` 为复合主键之一，但程序蓝图中的 `dormitory_config` 表仅列出了 `character_id` 作为主键，未提及 `player_id`，这将导致多玩家数据冲突。
- 修改建议: 在 `dormitory_config` 表定义中，将复合主键明确为 `(player_id, character_id)`，并补充 `player_id` 字段的类型定义（字符串）。
### Issue 2 [严重级别: 致命]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、 前后端通信协议 (API & 数据对接)
- 问题描述: 所有 API 接口的请求参数中均缺少 `player_id`。由于数据以 `player_id + character_id` 为复合主键，服务端需要 `player_id` 来正确路由和校验数据。缺少该参数会导致服务端无法确定是哪个玩家的数据，所有接口均无法正常工作。
- 修改建议: 在所有 API 接口的请求参数中增加 `player_id` 字段。例如 `Dormitory_LoadScene` 的请求参数应为 `player_id, character_id`。
### Issue 3 [严重级别: 致命]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、 前后端通信协议 (API & 数据对接)
- 问题描述: 系统策划案中描述了 `Dormitory_SwitchTemplate` 接口应返回“无法适配的家具ID列表”，但程序蓝图中的该接口返回参数仅写了“成功/失败”，缺少了必要的 `unadapted_furniture_ids` 字段。前端需要此列表来向玩家展示哪些家具被回收至背包。
- 修改建议: 在 `Dormitory_SwitchTemplate` 接口的返回参数中增加 `unadapted_furniture_ids`（字符串数组），用于返回无法适配新场景模板的家具ID列表。
### Issue 4 [严重级别: 高]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 三、 后端逻辑划分 (Server) -> 核心校验逻辑
- 问题描述: 后端核心校验逻辑中提到了“方案名称是否重复”校验，但系统策划案和数值说明书中均未定义方案名称的唯一性范围（是全局唯一、角色内唯一还是玩家内唯一）。这会导致实现歧义，可能引发数据冲突或逻辑错误。
- 修改建议: 在系统策划案或数值说明书中明确方案名称的唯一性范围（建议为“同一角色下方案名称唯一”），并在程序蓝图中更新校验逻辑的描述以匹配该规则。
### Issue 5 [严重级别: 高]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 三、 后端逻辑划分 (Server) -> 核心校验逻辑
- 问题描述: 系统策划案中描述了“若玩家在切换方案时未保存当前状态，系统自动保存当前状态为临时方案”，程序蓝图也实现了 `Dormitory_SaveTemporaryScheme` 等接口。但系统策划案中未定义临时方案的保存时机和覆盖规则（例如：是每次切换方案时都保存，还是仅在退出宿舍时保存？）。这会导致前端实现与后端预期不一致。
- 修改建议: 在系统策划案中明确临时方案的保存触发时机（例如：每次切换方案或退出宿舍时自动保存），并在程序蓝图中更新相关逻辑描述以对齐。
**当前审查总计问题:** 5 个

--- 审查时间: 2026-06-03 17:17:13 ---
### Issue 1 [严重级别: 致命]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 三、后端逻辑划分 (Server) - 持久化数据 (DB)
- 问题描述: 后端持久化字段 `current_selected_character_id` 与系统策划案及数值说明书中的定义冲突。系统策划案 2.1 节明确该字段为运行时状态（每次选择角色时更新），不应持久化到 `player_character_dormitory` 主表中。该字段应存储在客户端内存或会话缓存中，持久化会导致每次加载场景时都需额外查询，且与复合主键设计矛盾（一个玩家+角色组合只能有一个当前选中角色，但复合主键下每个角色都有一条记录，逻辑上无法确定全局当前选中角色）。
- 修改建议: 将 `current_selected_character_id` 从 `player_character_dormitory` 表中移除。改为在玩家全局配置表或客户端本地存储中维护该字段。后端只需在 `Dormitory_LoadScene` 接口中接收该参数作为请求参数即可。
### Issue 2 [严重级别: 致命]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、前后端通信协议 (API & 数据对接) - Dormitory_GetUnlockedContent
- 问题描述: API `Dormitory_GetUnlockedContent` 的返回参数中包含了 `unlocked_effects`（特效）字段，但系统策划案和数值配表中均未定义任何特效数据。系统策划案 4.2 节虽然提到了“滤镜与特效”作为付费点，但数值配表中只有 `free_filters` 数组，没有 `free_effects` 或任何特效相关的配置表。该 API 返回了一个不存在的数据结构，会导致前端请求后收到空数组或解析错误。
- 修改建议: 要么从 API 返回参数中移除 `unlocked_effects` 字段，要么由数值策划在 `system_numerical_data.json` 中补充特效相关的配置表（如 `free_effects` 数组），并确保系统策划案中明确特效的获取与使用逻辑。
### Issue 3 [严重级别: 高]
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 2.8 方案保存与切换
- 问题描述: 系统策划案 2.8 节描述了方案保存与切换逻辑，但未定义方案删除后的具体数据清理规则。当玩家删除一个方案时，该方案对应的 `character_scheme_data` 中的记录被移除，但方案保存时自动生成的缩略图（由程序蓝图中的方案缩略图生成器产生）是否应同步删除？若缩略图残留，会导致存储空间浪费和潜在的数据不一致。
- 修改建议: 在系统策划案中补充方案删除的完整数据清理规则：明确删除方案时是否同步删除对应的缩略图文件，以及缩略图的存储路径和命名规则。
### Issue 4 [严重级别: 高]
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 三、后端逻辑划分 (Server) - 核心校验逻辑 - 临时方案保存规则
- 问题描述: 临时方案保存规则中，保存时机包括“退出宿舍场景时”和“切换角色时”，但程序蓝图中的 API 列表缺少一个在退出场景或切换角色时调用的接口。当前 API 中 `Dormitory_SaveTemporaryScheme` 可以保存临时方案，但系统策划案和蓝图均未定义在退出/切换时由谁触发该 API 调用。若由前端在退出时主动调用，则存在网络延迟或断线导致数据丢失的风险。
- 修改建议: 在 `Dormitory_LoadScene` 接口的请求参数中增加一个 `save_temporary_before_load` 布尔字段，允许前端在加载新场景前，将当前场景的临时方案数据一并提交，由后端在同一个事务中完成旧临时方案的保存和新场景的加载，确保数据一致性。
### Issue 5 [严重级别: 中]
- 责任方: ux_agent
- 目标文件: ui_interaction_blueprint.md
- 锚点: 界面三：宿舍场景主界面 - 核心交互需求表
- 问题描述: UX 蓝图在界面三（宿舍场景主界面）中列出了“隐藏UI”和“重置视角”按钮，但系统策划案 3.3 节和 3.1 节中明确这些功能应存在于设置面板中（UI透明度调整）或作为独立操作（视角重置）。UX 蓝图将这些功能直接放在主场景 HUD 上作为常驻按钮，与系统策划案的设计意图不符。系统策划案强调“半透明毛玻璃设计，不遮挡角色主体”，增加常驻按钮会占用屏幕空间，违背设计目标。
- 修改建议: 将“隐藏UI”和“重置视角”功能移入设置面板或通过长按/双击等手势触发，而非作为常驻按钮显示在主场景 HUD 上。UX Agent 应修改蓝图，移除这两个常驻按钮，改为在设置面板中提供对应选项。
**当前审查总计问题:** 5 个
