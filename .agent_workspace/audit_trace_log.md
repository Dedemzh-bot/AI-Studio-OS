
--- 审查时间: 2026-05-27 17:15:25 ---
### Issue 1
- 责任方: numerical_planner
- 目标文件: 数值配表 (data.json)
- 锚点: continuous_formulas.stats_board.pve_win_rate.base
- 问题描述: 数值配表中 `pve_win_rate` 的 `base` 值为 0.5，但数值说明书中 `pve_win_rate` 的默认值为 0.0。两者不一致。
- 修改建议: 请确认 `pve_win_rate` 的初始默认值应为 0.0 还是 0.5，并统一数值说明书和数值配表中的定义。
### Issue 2
- 责任方: numerical_planner
- 目标文件: 数值配表 (data.json)
- 锚点: continuous_formulas.stats_board.pvp_win_rate.base
- 问题描述: 数值配表中 `pvp_win_rate` 的 `base` 值为 0.5，但数值说明书中 `pvp_win_rate` 的默认值为 0.0。两者不一致。
- 修改建议: 请确认 `pvp_win_rate` 的初始默认值应为 0.0 还是 0.5，并统一数值说明书和数值配表中的定义。
### Issue 3
- 责任方: numerical_planner
- 目标文件: 数值配表 (data.json)
- 锚点: continuous_formulas.stats_board.character_collection_rate.base
- 问题描述: 数值配表中 `character_collection_rate` 的 `base` 值为 0.0，但数值说明书中 `character_collection_rate` 的默认值为 0.0。此字段一致。但数值配表中存在 `growth` 字段，而数值说明书中未提及收集率的增长逻辑。数值配表中的 `growth` 字段含义不明，与策划案中“收集率计算”逻辑不符。
- 修改建议: 请明确 `character_collection_rate` 的 `growth` 字段在系统中的具体作用，或将其移除，因为策划案中收集率是动态计算的，而非线性增长。
### Issue 4
- 责任方: numerical_planner
- 目标文件: 数值配表 (data.json)
- 锚点: continuous_formulas.stats_board.weapon_collection_rate.base
- 问题描述: 数值配表中 `weapon_collection_rate` 的 `base` 值为 0.0，但数值说明书中 `weapon_collection_rate` 的默认值为 0.0。此字段一致。但数值配表中存在 `growth` 字段，而数值说明书中未提及收集率的增长逻辑。数值配表中的 `growth` 字段含义不明，与策划案中“收集率计算”逻辑不符。
- 修改建议: 请明确 `weapon_collection_rate` 的 `growth` 字段在系统中的具体作用，或将其移除，因为策划案中收集率是动态计算的，而非线性增长。
### Issue 5
- 责任方: system_planner
- 目标文件: 系统策划案 (system_design_detail.md)
- 锚点: 数据统计看板模块
- 问题描述: 策划案中数据统计看板模块的【前置条件】为“玩家等级≥10级”，但数值说明书和程序蓝图中均未提及此等级限制。这可能导致低等级玩家无法访问该模块，但后端数据接口和前端组件并未对此进行限制。
- 修改建议: 请在数值说明书或程序蓝图中明确数据统计看板模块的等级解锁条件，并确保后端API和前端UI组件在玩家等级不足时进行相应处理（如隐藏或显示锁定状态）。
### Issue 6
- 责任方: system_planner
- 目标文件: 系统策划案 (system_design_detail.md)
- 锚点: 历史战绩模块
- 问题描述: 策划案中历史战绩模块的【前置条件】为“玩家完成至少1场高光战绩”，但数值说明书和程序蓝图中均未提及此条件。这可能导致无高光战绩的玩家无法访问该模块，但后端数据接口和前端组件并未对此进行限制。
- 修改建议: 请在数值说明书或程序蓝图中明确历史战绩模块的解锁条件，并确保后端API和前端UI组件在玩家无高光战绩时进行相应处理（如显示占位文字）。
### Issue 7
- 责任方: system_planner
- 目标文件: 系统策划案 (system_design_detail.md)
- 锚点: 社交互动模块
- 问题描述: 策划案中社交互动模块的【前置条件】为“玩家已添加至少1名好友”，但数值说明书和程序蓝图中均未提及此条件。这可能导致无好友的玩家无法访问该模块，但后端数据接口和前端组件并未对此进行限制。
- 修改建议: 请在数值说明书或程序蓝图中明确社交互动模块的解锁条件，并确保后端API和前端UI组件在玩家无好友时进行相应处理（如隐藏或显示引导文字）。
### Issue 8
- 责任方: tech_architect
- 目标文件: 程序蓝图 (tech_blueprint.md)
- 锚点: 四、 前后端通信协议 (API & 数据对接) > 4.1 核心接口定义 > 1. 获取主页数据
- 问题描述: 程序蓝图中的“获取主页数据”接口返回参数中包含了 `stats_board` 和 `battle_history` 数据，但策划案中这两个模块的数据是独立刷新或加载的（数据统计每24小时刷新，历史战绩从战斗系统读取）。此接口设计将所有数据打包返回，与策划案中模块化的数据加载逻辑不符。
- 修改建议: 请考虑将 `stats_board` 和 `battle_history` 的数据获取拆分为独立的API接口，或明确此接口在何种场景下被调用（如首次进入主页时），并确保与策划案中的数据加载逻辑一致。
### Issue 9
- 责任方: tech_architect
- 目标文件: 程序蓝图 (tech_blueprint.md)
- 锚点: 四、 前后端通信协议 (API & 数据对接) > 4.1 核心接口定义 > 1. 获取主页数据
- 问题描述: 程序蓝图中的“获取主页数据”接口返回参数中包含了 `social_interaction` 的 `messages` 字段，但策划案中留言板只显示最近20条已审核通过的留言。此接口设计返回所有留言数据，可能导致数据量过大，且未考虑审核状态过滤。
- 修改建议: 请修改接口设计，使其只返回已审核通过的留言，并限制返回条数（如20条），或增加分页参数。
### Issue 10
- 责任方: tech_architect
- 目标文件: 程序蓝图 (tech_blueprint.md)
- 锚点: 五、 数值与配置表挂载 > 5.1 配置表读取方式
- 问题描述: 程序蓝图中的配置表读取方式示例中，`main_squad` 的 `lod_memory_thresholds` 字段使用了内存阈值（如2048、1024），但策划案中【边界与异常兜底】描述的是“设备内存<2GB”和“内存<1GB”，单位不一致。
- 修改建议: 请统一内存阈值的单位，建议使用MB（兆字节）或GB（吉字节），并确保与策划案中的描述一致。
### Issue 11
- 责任方: tech_architect
- 目标文件: 程序蓝图 (tech_blueprint.md)
- 锚点: 五、 数值与配置表挂载 > 5.1 配置表读取方式
- 问题描述: 程序蓝图中的配置表读取方式示例中，`achievement_wall` 的 `max_display_order` 字段值为100，但策划案中并未提及排序数组的最大长度。此限制可能影响玩家自定义排序的体验。
- 修改建议: 请确认 `max_display_order` 的必要性，如果存在，请在策划案中补充说明，或将其移除。
### Issue 12
- 责任方: system_planner
- 目标文件: 系统策划案 (system_design_detail.md)
- 锚点: 主力阵容展示模块
- 问题描述: 策划案中主力阵容展示模块的【边界与异常兜底】提到“若玩家分解了阵容中的角色，系统自动将该槽位设为‘空’”，但程序蓝图和数值说明书中均未定义当角色被分解时，后端应如何处理 `main_squad` 表中的数据。
- 修改建议: 请在程序蓝图中明确角色分解时对 `main_squad` 表的影响，例如在角色删除逻辑中增加对 `main_squad` 表的级联更新操作。
### Issue 13
- 责任方: system_planner
- 目标文件: 系统策划案 (system_design_detail.md)
- 锚点: 历史战绩模块
- 问题描述: 策划案中历史战绩模块的【边界与异常兜底】提到“若某条置顶战绩因版本更新而失效，系统自动取消其置顶状态”，但程序蓝图和数值说明书中均未定义如何判断战绩是否“失效”，以及如何触发自动取消置顶的逻辑。
- 修改建议: 请在程序蓝图中明确战绩失效的判断标准（如活动ID过期）和自动取消置顶的触发机制（如每日检查或版本更新时）。
**当前审查总计问题:** 13 个

--- 审查时间: 2026-05-27 18:52:43 ---
### Issue 1
- 责任方: numerical_planner
- 目标文件: 数值配表 (data.json)
- 锚点: continuous_formulas.dormitory_affection_level.formula
- 问题描述: 好感度等级公式与策划案中明确列出的里程碑数值严重冲突。策划案中等级1-10所需经验值分别为：0, 100, 200, 400, 700, 1100, 1600, 2200, 2900, 3700, 4600。而数值配表中使用的连续公式 `floor(1 + 0.5 * ln(dormitory_affection + 1))` 计算出的等级与这些里程碑数值完全不匹配。例如，当好感度为100时，公式计算结果为 `floor(1 + 0.5 * ln(101)) ≈ floor(1 + 0.5 * 4.615) = floor(3.307) = 3`，但策划案中100点应为等级2。
- 修改建议: 请数值策划重新审查好感度等级的计算逻辑。要么放弃连续公式，直接使用策划案中定义的离散里程碑表；要么调整连续公式的参数，使其计算结果与策划案中的里程碑数值对齐。
### Issue 2
- 责任方: numerical_planner
- 目标文件: 数值配表 (data.json)
- 锚点: discrete_milestones.dormitory_affection_level
- 问题描述: 数值配表中的解锁标志与策划案不一致。1. 策划案中等级3解锁'腰部触摸区域'，配表中正确标记了 `unlocked_touch_waist`，但策划案中等级5解锁的是'居家服'，配表中标记为 `unlocked_costume_casual`，字段名不一致。2. 策划案中等级8解锁'睡衣'和'特殊组合交互'，配表中标记为 `unlocked_costume_pajama` 和 `unlocked_special_interaction`，但策划案中'特殊组合交互'的解锁条件明确为'好感度等级≥8且拥有床、枕头、被子家具'，配表中缺少对家具条件的说明。3. 策划案中等级9和10解锁的是'角色专属剧情片段1和2'以及'告白特殊互动'，配表中标记为 `unlocked_story_1`, `unlocked_story_2`, `unlocked_confession`，这些字段在数值说明书的 `field_dictionary` 中完全不存在。
- 修改建议: 请数值策划：1. 统一服装解锁标志的命名（策划案中为'居家服'，配表中为'casual'，建议统一为 `unlocked_costume_home` 或与策划案一致）。2. 在 `relations_and_enums` 中明确特殊组合交互的家具条件。3. 在 `field_dictionary` 中补充 `unlocked_story_1`, `unlocked_story_2`, `unlocked_confession` 等字段的定义。
### Issue 3
- 责任方: numerical_planner
- 目标文件: 数值说明书 (system_numerical_docs.json)
- 锚点: field_dictionary.unlocked_flag
- 问题描述: 数值说明书中定义了一个泛化的 `unlocked_flag` 字段，描述为'用于affection_unlock_content_table模块'，但该字段过于笼统，无法对应到具体的解锁内容。策划案中每个解锁项（如胸部触摸、睡衣、剧情等）都有独立的 `unlocked_` 前缀字段，而数值说明书中只定义了 `unlocked_touch_chest` 和 `unlocked_costume_pajama`，缺少 `unlocked_touch_waist`, `unlocked_touch_leg`, `unlocked_costume_casual`（或 `unlocked_costume_home`）, `unlocked_story_1`, `unlocked_story_2`, `unlocked_confession`, `unlocked_special_interaction` 等字段。
- 修改建议: 请数值策划在 `field_dictionary` 中补充所有策划案中提到的解锁标志字段，并删除或明确泛化的 `unlocked_flag` 字段。
### Issue 4
- 责任方: system_planner
- 目标文件: 系统策划案 (system_design_detail.md)
- 锚点: 好感度成长系统
- 问题描述: 策划案中好感度等级经验值表与数值配表中的里程碑数值存在矛盾。策划案中明确列出了10个等级的经验值：1级:100, 2级:200, 3级:400, 4级:700, 5级:1100, 6级:1600, 7级:2200, 8级:2900, 9级:3700, 10级:4600。但按照常规理解，'1级:100'通常意味着从0到100点好感度对应等级1，100到200对应等级2，以此类推。然而，数值配表中的 `required_affection` 值（0, 100, 200, 400, 700, 1100, 1600, 2200, 2900, 3700）与策划案中的经验值列表（100, 200, 400, 700, 1100, 1600, 2200, 2900, 3700, 4600）在数值上错位了一位。策划案中第10级需要4600点，但配表中最高只到3700。
- 修改建议: 请系统策划与数值策划对齐好感度等级的定义。明确'1级:100'是指'达到100点好感度时升到1级'还是'1级需要100点经验值'。如果是前者，配表中的 `required_affection` 值是正确的（0->1级, 100->2级, ...）；如果是后者，配表需要调整。同时，策划案中第10级的4600点需要确认是否遗漏。
### Issue 5
- 责任方: tech_architect
- 目标文件: 程序蓝图 (tech_blueprint.md)
- 锚点: 五、数值与配置表挂载 - 1. 好感度等级经验值表
- 问题描述: 程序蓝图直接引用了策划案中的好感度等级经验值表（level_1:100, level_2:200, ... level_10:4600），但数值配表中使用的是完全不同的连续公式。程序蓝图要求'实现为连续公式，避免硬编码枚举'，但数值配表中的连续公式与策划案中的离散值不兼容。程序将无法确定应该使用哪个数据源。
- 修改建议: 请技术架构师与数值策划协调，确定最终采用离散里程碑还是连续公式。如果采用离散里程碑，程序蓝图应直接引用数值配表中的 `discrete_milestones.dormitory_affection_level` 数据；如果采用连续公式，则需要数值策划修正公式使其与策划案对齐。
### Issue 6
- 责任方: tech_architect
- 目标文件: 程序蓝图 (tech_blueprint.md)
- 锚点: 三、后端逻辑划分 - 角色宿舍数据表
- 问题描述: 程序蓝图中的角色宿舍数据表缺少多个策划案中明确提到的字段。策划案中提到了 `last_touch_time`, `touch_count_today`, `rejected_touch_count`, `touch_cooldown`, `last_interaction_time`, `interaction_count_today`, `interaction_cooldown`, `special_interaction_unlocked`, `last_special_interaction_time` 等字段，但程序蓝图中的角色宿舍数据表只包含了 `dormitory_affection`, `dormitory_affection_level`, `unlocked_touch_chest`, `unlocked_costume_pajama`, `special_interaction_unlocked`, `last_special_interaction_time`, `room_layout`, `theme_set_active`。触摸和交互相关的冷却/计数/时间戳字段完全缺失。
- 修改建议: 请技术架构师在角色宿舍数据表中补充 `last_touch_time`, `touch_count_today`, `rejected_touch_count`, `last_interaction_time`, `interaction_count_today` 等字段。注意 `touch_cooldown` 和 `interaction_cooldown` 是运行时状态，不应持久化。
### Issue 7
- 责任方: tech_architect
- 目标文件: 程序蓝图 (tech_blueprint.md)
- 锚点: 三、后端逻辑划分 - 玩家宿舍解锁状态表
- 问题描述: 程序蓝图中的玩家宿舍解锁状态表缺少 `dormitory_pass` 字段。策划案中明确提到玩家背包中需要拥有'私人宿舍通行证'道具，且数值说明书中的 `field_dictionary` 也定义了 `dormitory_pass` 字段。程序蓝图在背包道具表中提到了 `dormitory_pass`，但在玩家宿舍解锁状态表中没有体现该道具的持有状态。
- 修改建议: 请技术架构师在玩家宿舍解锁状态表中增加 `dormitory_pass` 字段，或明确说明该字段由背包系统管理，并在核心校验逻辑中引用背包系统的接口。
### Issue 8
- 责任方: tech_architect
- 目标文件: 程序蓝图 (tech_blueprint.md)
- 锚点: 四、前后端通信协议 - Dormitory_TouchCharacter
- 问题描述: `Dormitory_TouchCharacter` 接口的返回参数中包含了 `rejected` 字段，但缺少 `rejected_touch_count` 的返回。策划案中明确提到拒绝次数超过5次后当日触摸不再增加好感度，客户端需要知道当前的拒绝次数以显示提示。
- 修改建议: 请技术架构师在 `Dormitory_TouchCharacter` 的返回参数中增加 `rejected_touch_count` 字段，以便客户端在拒绝次数达到上限时显示相应提示。
### Issue 9
- 责任方: tech_architect
- 目标文件: 程序蓝图 (tech_blueprint.md)
- 锚点: 四、前后端通信协议 - Dormitory_GetWeatherTime
- 问题描述: `Dormitory_GetWeatherTime` 接口返回了 `character_state`，但策划案中角色状态是由游戏内时间 `in_game_time` 决定的，客户端可以根据时间自行计算。服务端返回 `character_state` 可能导致客户端与服务端状态不一致（例如在时间边界附近）。
- 修改建议: 请技术架构师考虑是否由客户端根据 `in_game_time` 自行计算 `character_state`，或者服务端返回 `in_game_time` 和 `current_weather` 后，客户端根据策划案中的时间映射表自行推导角色状态。这样可以减少网络传输和状态同步问题。
### Issue 10
- 责任方: system_planner
- 目标文件: 系统策划案 (system_design_detail.md)
- 锚点: 好感度解锁内容表
- 问题描述: 策划案中好感度解锁内容表与数值配表中的解锁条件存在不一致。策划案中等级2解锁'物品交互（床、沙发）'，等级4解锁'物品交互（书桌、玩偶）'，等级6解锁'物品交互（书架、窗户）'。但数值配表中的 `discrete_milestones` 没有为等级2、4、6设置任何解锁标志（`unlock_flags: []`），这意味着物品交互的解锁条件在数值配表中完全没有体现。
- 修改建议: 请系统策划与数值策划对齐，在数值配表的 `discrete_milestones` 中为等级2、4、6添加对应的物品交互解锁标志（如 `unlocked_interact_bed`, `unlocked_interact_desk` 等），或者在策划案中明确物品交互的解锁不由好感度等级控制。
### Issue 11
- 责任方: system_planner
- 目标文件: 系统策划案 (system_design_detail.md)
- 锚点: 好感度成长系统
- 问题描述: 策划案中好感度每日上限为100点（所有角色共享），但触摸每日上限为50次（每次+1点），交互每日上限为30次（每次+2点）。理论上，如果玩家完成所有触摸（50点）和交互（60点），单日可获得110点好感度，超过了100点的每日上限。这会导致玩家在完成所有触摸和部分交互后，后续交互不再增加好感度，但交互次数仍被消耗，造成玩家困惑。
- 修改建议: 请系统策划调整数值：要么降低触摸或交互的每日次数上限（如触摸40次、交互25次），要么提高每日好感度上限（如150点），或者明确说明当好感度达到每日上限后，触摸和交互仍消耗次数但不增加好感度。
### Issue 12
- 责任方: numerical_planner
- 目标文件: 数值说明书 (system_numerical_docs.json)
- 锚点: field_dictionary.battle_reward_trigger
- 问题描述: 数值说明书中定义了 `battle_reward_trigger` 字段，描述为'标记战斗结算联动内容是否已触发'，但程序蓝图中使用的是 `battle_reward_triggered_count`（整数，每日上限5次）。这两个字段类型不一致（布尔 vs 整数），且策划案中明确要求每日上限5次，布尔值无法满足计数需求。
- 修改建议: 请数值策划将 `battle_reward_trigger` 的类型从布尔值改为整数，并重命名为 `battle_reward_triggered_count`，与程序蓝图保持一致。
### Issue 13
- 责任方: tech_architect
- 目标文件: 程序蓝图 (tech_blueprint.md)
- 锚点: 三、后端逻辑划分 - 核心校验逻辑 - 战斗结算联动校验
- 问题描述: 程序蓝图中的战斗结算联动校验逻辑与策划案不完全一致。策划案中明确要求'若多个角色满足条件，优先播放好感度等级最高的角色内容'，但程序蓝图中的校验逻辑只提到了'选择好感度等级最高的角色'，没有处理等级相同的情况。策划案中边界与异常兜底部分提到'多个角色等级相同：随机选择一个角色触发'。
- 修改建议: 请技术架构师在战斗结算联动校验逻辑中补充：当多个角色好感度等级相同时，随机选择一个角色触发联动内容。
### Issue 14
- 责任方: system_planner
- 目标文件: 系统策划案 (system_design_detail.md)
- 锚点: 昼夜与天气系统
- 问题描述: 策划案中天气系统描述为'每现实4小时随机切换一次天气'，但数值配表中的 `current_weather` 里程碑也设置了 `duration_hours: 4`。然而，策划案中没有说明天气切换的具体逻辑（例如，是否允许连续两次出现同一种天气？切换时是否有权重？）。此外，策划案中天气类型有5种（晴天、多云、小雨、大雨、雪天），但程序蓝图中没有提到天气切换的随机算法。
- 修改建议: 请系统策划补充天气切换的详细规则：是否允许重复？每种天气的出现概率是否相等？是否需要根据季节或地区调整？这些信息对程序实现至关重要。
### Issue 15
- 责任方: tech_architect
- 目标文件: 程序蓝图 (tech_blueprint.md)
- 锚点: 二、前端模块划分 - 表现层控制器 - CharacterDormitoryController
- 问题描述: 程序蓝图中的 `CharacterDormitoryController` 负责播放触摸反馈动作/表情/语音，但缺少对'拒绝反馈'的详细处理逻辑。策划案中明确提到当触摸不允许时触发'拒绝反馈'（角色躲闪、摇头、语音提示'不要这样'），且拒绝次数超过5次后当日所有触摸区域均视为不允许。程序蓝图中没有说明拒绝反馈的触发条件和次数限制。
- 修改建议: 请技术架构师在 `CharacterDormitoryController` 或 `TouchRaycastController` 中补充拒绝反馈的处理逻辑：当触摸区域未解锁或拒绝次数超过5次时，播放拒绝反馈动画/语音，并更新 `rejected_touch_count`。
**当前审查总计问题:** 15 个

--- 审查时间: 2026-05-28 01:59:13 ---
### Issue 1
- 责任方: system_planner
- 目标文件: 系统策划案
- 锚点: 个人主页（名片）系统 - 展示内容定义
- 问题描述: 策划案中【展示内容列表】提到了“动态头像框”和“特效称号”，但在【数据状态变化】中，`player_homepage_config` 表记录的字段包含了“头像框ID”，却没有“特效称号ID”。特效称号作为一个独立的展示项，其ID未被记录在主页配置中，导致数据状态变化与展示内容不一致。
- 修改建议: 建议在 `player_homepage_config` 的数据状态变化描述中，增加“特效称号ID”字段，确保所有展示项都有对应的数据记录字段。
### Issue 2
- 责任方: system_planner
- 目标文件: 系统策划案
- 锚点: 个人主页（名片）系统 - 展示内容定义
- 问题描述: 策划案中【展示内容列表】提到了“角色皮肤”和“角色动作”，但在【数据状态变化】中，`player_homepage_config` 表记录的字段包含了“皮肤ID”和“动作ID”。然而，在【边界与异常兜底】中，只提到了“玩家删除已装备为展示角色的角色时，系统自动将展示角色重置为默认角色”和“玩家删除已装备皮肤的角色时，系统自动将皮肤重置为默认皮肤”，却没有提及“玩家删除已装备动作的角色时，系统自动将动作重置为默认动作”。逻辑不完整。
- 修改建议: 建议在【边界与异常兜底】中补充：当玩家删除已装备动作的角色时，系统自动将动作重置为默认动作。
### Issue 3
- 责任方: numerical_planner
- 目标文件: 数值说明书
- 锚点: field_dictionary
- 问题描述: 数值说明书中 `field_dictionary` 定义了 `player_homepage_config` 对象，包含 `avatar_id`, `title_id`, `signature_text`, `background_id`, `display_character_id`, `skin_id`, `action_id`, `avatar_frame_id`。但策划案中明确提到了“特效称号”是一个独立的展示项，而数值说明书中没有对应的字段（如 `effect_title_id`）来记录特效称号的ID。这导致数值说明书与策划案不一致。
- 修改建议: 建议在 `player_homepage_config` 对象中增加 `effect_title_id` 字段，并定义其类型、取值范围和默认值，以匹配策划案中的“特效称号”展示项。
### Issue 4
- 责任方: numerical_planner
- 目标文件: 数值说明书
- 锚点: field_dictionary
- 问题描述: 数值说明书中 `field_dictionary` 定义了 `player_statistics` 对象，其字段包含 `main_stage`, `abyss_floor`, `character_collection_pct`, `max_constellation_count`, `max_level_count`, `login_days`, `weekly_activity`。但策划案中【成就/战绩系统 - 展示内容列表】提到的“角色收集度百分比”在数值说明书中对应 `character_collection_percentage`，而 `player_statistics` 中却使用了 `character_collection_pct`，字段命名不一致。这可能导致程序开发时引用错误。
- 修改建议: 建议统一字段命名，将 `player_statistics` 中的 `character_collection_pct` 改为 `character_collection_percentage`，以保持与 `field_dictionary` 中其他字段的命名风格一致，并匹配策划案中的描述。
### Issue 5
- 责任方: numerical_planner
- 目标文件: 数值配表
- 锚点: continuous_formulas
- 问题描述: 数值配表中 `continuous_formulas` 定义了 `player_statistics` 的初始值 `{"main_stage":0,"abyss_floor":0,"character_collection_pct":0.0,"max_constellation_count":0,"max_level_count":0,"login_days":0,"weekly_activity":0}`。但数值说明书 `field_dictionary` 中 `player_statistics` 的描述是“包含主线最高章节、深渊最高层数、角色收集度、满命角色数、满级角色数、累计登录天数、本周活跃度等字段”，而配表中的字段名 `character_collection_pct` 与说明书中的 `character_collection_percentage` 不一致。
- 修改建议: 建议将数值配表中 `player_statistics` 的初始值字段名 `character_collection_pct` 修改为 `character_collection_percentage`，以保持与数值说明书一致。
### Issue 6
- 责任方: tech_architect
- 目标文件: 程序蓝图
- 锚点: 四、 前后端通信协议 (API & 数据对接)
- 问题描述: 程序蓝图中的API列表没有提供获取“特效称号”相关数据的接口。策划案中明确提到了“特效称号”作为个人主页的一个独立展示项，且数值说明书中也应有对应的字段。但蓝图中的 `GetHomepageConfig` 和 `SaveHomepageConfig` 接口没有包含 `effect_title_id` 参数，也没有提供获取玩家已拥有特效称号列表的接口。这导致策划案中的功能无法通过现有API实现。
- 修改建议: 建议在 `SaveHomepageConfig` 接口的请求参数中增加 `effect_title_id`，并新增一个 `GetPlayerOwnedEffectTitles` 接口，用于获取玩家已拥有的特效称号列表，以便前端进行校验和展示。
### Issue 7
- 责任方: tech_architect
- 目标文件: 程序蓝图
- 锚点: 三、 后端逻辑划分 (Server)
- 问题描述: 程序蓝图中的【核心校验逻辑】部分，对于主页配置保存的校验，只校验了 `display_character_id`, `skin_id`, `action_id` 以及 `avatar_id`, `title_id`, `background_id`, `avatar_frame_id` 是否在对应的拥有列表中。但缺少对 `effect_title_id`（特效称号）的校验。如果后续增加了特效称号功能，后端将无法防止玩家设置未拥有的特效称号。
- 修改建议: 建议在【核心校验逻辑】中增加对 `effect_title_id` 的校验，验证其是否在玩家已拥有的特效称号列表中。
### Issue 8
- 责任方: tech_architect
- 目标文件: 程序蓝图
- 锚点: 五、 数值与配置表挂载
- 问题描述: 程序蓝图中的【配置表数据结构映射】部分，定义了 `id_ranges` 包含 `avatar`, `title`, `background`, `avatar_frame`, `character`, `skin`, `action`，但没有包含 `effect_title`（特效称号）的ID范围。这会导致程序在加载配置时，无法对特效称号的ID进行合法性校验。
- 修改建议: 建议在 `id_ranges` 中增加 `effect_title` 字段，并定义其取值范围（如 [1, 9999]），以匹配其他外观ID的配置方式。
**当前审查总计问题:** 8 个

--- 审查时间: 2026-05-28 13:29:36 ---
### Issue 1
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.affection_increment
- 问题描述: 数值说明书中定义 affection_increment 为每次互动或小游戏结算时增加的好感度经验值，范围10-100，默认值为10。但策划案中互动热点系统固定增加10点，小游戏系统根据得分等级增加30-100点，两者含义不同，应拆分为两个字段或明确区分。
- 修改建议: 建议将 affection_increment 拆分为 interaction_affection_increment（固定10点）和 minigame_affection_increment（动态30-100点），或增加说明字段区分来源。
### Issue 2
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.experience_to_next_level
- 问题描述: 数值说明书中定义 experience_to_next_level 为升到下一级所需的总经验值，公式为 (affection_level + 1) * 100，范围100-1000。但策划案中好感度系统描述为“每级所需经验呈线性增长（1级需100经验，10级需1000经验）”，未明确是累计经验还是单级经验。若为单级经验，则10级需1000经验，但总经验应为5500，与公式含义冲突。
- 修改建议: 建议明确 experience_to_next_level 是单级所需经验还是累计到下一级的总经验，并调整公式或描述以保持一致。
### Issue 3
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.special_event_trigger_level
- 问题描述: 数值说明书中定义 special_event_trigger_level 为触发特殊事件的好感度等级，默认值为0。但策划案中好感度系统明确特殊事件触发等级为5、8、10，且数值配表中 special_event_trigger_level 的 base 为5，growth 为3，生成序列为5,8,11...，与策划案10级上限不符，且缺少10级事件。
- 修改建议: 建议将 special_event_trigger_level 改为离散里程碑列表 [5,8,10]，或调整 growth 使序列在10级内结束。
### Issue 4
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.story_unlock_affection_level_requirement
- 问题描述: 数值说明书中定义 story_unlock_affection_level_requirement 为解锁剧情片段所需的好感度等级，范围3-10，默认值为0。但策划案中剧情解锁系统明确5个剧情片段对应等级3、5、7、9、10，而数值配表中 story_unlock_affection_level_requirement 的 base 为3，growth 为2，生成序列为3,5,7,9,11...，与策划案10级上限不符，且缺少10级。
- 修改建议: 建议将 story_unlock_affection_level_requirement 改为离散里程碑列表 [3,5,7,9,10]，或调整 growth 使序列在10级内结束。
### Issue 5
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.minigame_unlock_affection_level
- 问题描述: 数值说明书中定义 minigame_unlock_affection_level 为解锁小游戏所需的好感度等级，范围0-10，默认值为0。但策划案中小游戏系统明确每个角色2-3个小游戏，初始解锁1个，其余需好感度等级达到3级和6级解锁，而数值配表中 minigame_unlock_affection_level 的 base 为0，growth 为3，生成序列为0,3,6,9...，与策划案初始解锁1个（等级0）和3级、6级解锁一致，但未明确只有3个等级点，且growth可能导致多余等级。
- 修改建议: 建议将 minigame_unlock_affection_level 改为离散里程碑列表 [0,3,6] 或明确只有3个等级点。
### Issue 6
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.behavior_trigger_probability
- 问题描述: 数值说明书中定义 behavior_trigger_probability 为当前AI行为的触发概率，默认值为0.3。但策划案中AI日常行为系统有7种行为，每种行为有独立概率（如看书30%、发呆20%等），而数值配表中 behavior_trigger_probability 的 base 为0.3，growth 为0.1，无法表示7种不同概率。
- 修改建议: 建议将 behavior_trigger_probability 改为对象或数组，存储每种行为的独立概率，如 {1:0.3, 2:0.2, 3:0.15, 4:0.1, 5:0.1, 6:0.05, 7:0.1}。
### Issue 7
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.voice_trigger_probability
- 问题描述: 数值说明书中定义 voice_trigger_probability 为当前AI行为触发语音的概率，默认值为0.1。但策划案中AI日常行为系统提到每个行为有预设语音列表，随机触发，触发概率可配置，未明确是全局概率还是每个行为独立概率。
- 修改建议: 建议明确 voice_trigger_probability 是全局概率还是每个行为独立，若独立则改为对象或数组。
### Issue 8
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.camera_zoom
- 问题描述: 数值说明书中定义 camera_zoom 为拍照模式下相机的缩放比例，范围0.5-5.0，默认值为1.0。但数值配表中 camera_zoom 的 base 为1.0，growth 为0.5，type 为 linear，暗示每次调整增加0.5，但策划案中未明确缩放步长，且范围0.5-5.0与线性增长不匹配。
- 修改建议: 建议将 camera_zoom 改为范围字段，或明确缩放步长和调整方式。
### Issue 9
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.selected_filter_id
- 问题描述: 数值说明书中定义 selected_filter_id 范围0-4，对应无滤镜、清新、复古、黑白、暖色，默认值为0。但数值配表中 selected_filter_id 的 base 为0，growth 为1，type 为 linear，暗示每次调整增加1，但策划案中未明确滤镜切换顺序或步长。
- 修改建议: 建议将 selected_filter_id 改为枚举类型，无需 growth 字段。
### Issue 10
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.selected_pose_id
- 问题描述: 数值说明书中定义 selected_pose_id 范围0-4，对应默认、站立、坐姿、躺姿、依靠，默认值为0。但数值配表中 selected_pose_id 的 base 为0，growth 为1，type 为 linear，暗示每次调整增加1，但策划案中未明确姿势切换顺序或步长。
- 修改建议: 建议将 selected_pose_id 改为枚举类型，无需 growth 字段。
### Issue 11
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.selected_expression_id
- 问题描述: 数值说明书中定义 selected_expression_id 范围0-4，对应默认、微笑、害羞、惊讶、眨眼，默认值为0。但数值配表中 selected_expression_id 的 base 为0，growth 为1，type 为 linear，暗示每次调整增加1，但策划案中未明确表情切换顺序或步长。
- 修改建议: 建议将 selected_expression_id 改为枚举类型，无需 growth 字段。
### Issue 12
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.screenshot_count
- 问题描述: 数值说明书中定义 screenshot_count 为拍照模式下已截图的累计数量，范围0-99999，默认值为0。但数值配表中 screenshot_count 的 base 为0，growth 为1，type 为 linear，暗示每次截图增加1，但策划案中未明确截图计数增长方式。
- 修改建议: 建议将 screenshot_count 改为简单计数器，无需 growth 字段。
### Issue 13
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.dlc_purchase_timestamp
- 问题描述: 数值说明书中定义 dlc_purchase_timestamp 为DLC购买时间戳，默认值为0。但数值配表中 dlc_purchase_timestamp 的 base 为0，growth 为1，type 为 linear，暗示每次购买增加1，但时间戳应为具体值，无需 growth。
- 修改建议: 建议将 dlc_purchase_timestamp 改为时间戳字段，无需 growth 字段。
### Issue 14
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.character_unlock_status
- 问题描述: 数值说明书中定义 character_unlock_status 为对象，键为角色ID，值为布尔，默认值为空对象。但数值配表中 character_unlock_status 的 base 为0，growth 为1，type 为 linear，与对象类型不匹配。
- 修改建议: 建议将 character_unlock_status 改为对象类型，无需 growth 字段。
### Issue 15
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.skin_unlock_status
- 问题描述: 数值说明书中定义 skin_unlock_status 为对象，键为皮肤ID，值为布尔，默认值为空对象。但数值配表中 skin_unlock_status 的 base 为0，growth 为1，type 为 linear，与对象类型不匹配。
- 修改建议: 建议将 skin_unlock_status 改为对象类型，无需 growth 字段。
### Issue 16
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.affection_reward_status
- 问题描述: 数值说明书中定义 affection_reward_status 为对象，键为等级，值为布尔，默认值为空对象。但数值配表中 affection_reward_status 的 base 为0，growth 为1，type 为 linear，与对象类型不匹配。
- 修改建议: 建议将 affection_reward_status 改为对象类型，无需 growth 字段。
### Issue 17
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.story_linkage_status
- 问题描述: 数值说明书中定义 story_linkage_status 为对象，键为剧情ID，值为布尔，默认值为空对象。但数值配表中 story_linkage_status 的 base 为0，growth 为1，type 为 linear，与对象类型不匹配。
- 修改建议: 建议将 story_linkage_status 改为对象类型，无需 growth 字段。
### Issue 18
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.souvenir_placement_position
- 问题描述: 数值说明书中定义 souvenir_placement_position 为对象，包含x、y、z三个浮点数，默认值为null。但数值配表中未包含此字段，导致缺失。
- 修改建议: 建议在数值配表中添加 souvenir_placement_position 字段，或明确其配置方式。
### Issue 19
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.souvenir_placement_rotation
- 问题描述: 数值说明书中定义 souvenir_placement_rotation 为对象，包含x、y、z三个浮点数，默认值为null。但数值配表中未包含此字段，导致缺失。
- 修改建议: 建议在数值配表中添加 souvenir_placement_rotation 字段，或明确其配置方式。
### Issue 20
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 互动热点系统
- 问题描述: 策划案中互动热点系统提到“部分热点需好感度等级解锁”，但未明确具体哪些热点需要解锁，以及解锁等级要求。数值说明书中 unlock_affection_level_requirement 默认值为0，但策划案中仅举例“躺在床上”需5级。
- 修改建议: 建议在策划案中补充所有互动热点的解锁等级要求列表，或明确配置方式。
### Issue 21
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 小游戏系统
- 问题描述: 策划案中小游戏系统提到每个角色2-3个小游戏，初始解锁1个，其余需好感度等级达到3级和6级解锁。但未明确具体小游戏名称或ID，以及每个角色的小游戏数量是否固定。
- 修改建议: 建议在策划案中补充每个角色的小游戏列表及解锁等级。
### Issue 22
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 好感度系统
- 问题描述: 策划案中好感度系统提到“好感度等级达到特定等级（如5级、8级、10级），触发特殊事件”，但未明确5级、8级、10级的具体事件内容（5级赠送纪念品，8级特殊互动动画，10级最终剧情片段），仅在数据状态变化中提及。
- 修改建议: 建议在流转逻辑中明确每个等级的特殊事件内容。
### Issue 23
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 剧情解锁系统
- 问题描述: 策划案中剧情解锁系统提到每个角色拥有5个剧情片段，分别对应好感度等级3、5、7、9、10。但未明确每个剧情片段是否需要小游戏成就，以及具体成就要求。
- 修改建议: 建议在策划案中补充每个剧情片段的解锁条件（好感度等级+小游戏成就）。
### Issue 24
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 纪念品系统
- 问题描述: 策划案中纪念品系统提到每个角色拥有10个纪念品，其中5个通过小游戏获得，5个通过好感度等级解锁。但未明确具体哪些纪念品通过小游戏获得，哪些通过好感度解锁，以及对应的好感度等级。
- 修改建议: 建议在策划案中补充纪念品列表及获取方式。
### Issue 25
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: AI日常行为系统
- 问题描述: 策划案中AI日常行为系统提到行为触发概率可配置，支持根据好感度等级调整概率（如高好感度增加“哼歌”概率）。但未明确具体调整规则或公式。
- 修改建议: 建议在策划案中补充概率调整规则或参考数值配置表。
### Issue 26
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心校验逻辑
- 问题描述: 程序蓝图中核心校验逻辑提到“好感度经验增长校验：每次互动/小游戏结算后，校验经验增加值是否与配置一致（互动固定10点，小游戏按得分等级）”，但未明确小游戏得分等级的具体校验逻辑（如S级100点+1碎片，A级80点等）。
- 修改建议: 建议在蓝图中补充小游戏得分等级奖励的校验逻辑，或引用数值配置表。
### Issue 27
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心校验逻辑
- 问题描述: 程序蓝图中核心校验逻辑提到“剧情解锁条件校验：校验好感度等级和小游戏成就是否达标”，但未明确小游戏成就的具体校验方式（如S级评价）。
- 修改建议: 建议在蓝图中补充小游戏成就的校验逻辑。
### Issue 28
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 CheckDLCStatus 接口的详细说明，如返回参数中是否包含购买平台。
- 修改建议: 建议在接口说明中补充 purchase_platform 字段。
### Issue 29
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 RecordInteraction 接口的详细说明，如是否返回冷却时间或解锁状态。
- 修改建议: 建议在接口说明中补充返回参数，如 cooldown_timer 或 hotspot_unlocked_flag。
### Issue 30
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 StartMinigame 接口的详细说明，如是否返回小游戏解锁状态或每日次数。
- 修改建议: 建议在接口说明中补充返回参数，如 minigame_unlocked_flag 和 daily_play_count。
### Issue 31
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 EndMinigame 接口的详细说明，如是否返回纪念品碎片数量或得分等级。
- 修改建议: 建议在接口说明中补充返回参数，如 score_grade 和 souvenir_fragment_count。
### Issue 32
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 CheckStoryUnlock 接口的详细说明，如是否返回小游戏成就要求。
- 修改建议: 建议在接口说明中补充返回参数，如 story_unlock_minigame_achievement_requirement。
### Issue 33
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 RecordStoryWatch 接口的详细说明，如是否返回奖励物品。
- 修改建议: 建议在接口说明中补充返回参数，如 reward_items。
### Issue 34
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 SynthesizeSouvenir 接口的详细说明，如是否返回纪念品模型数据。
- 修改建议: 建议在接口说明中补充返回参数，如 souvenir_model_data。
### Issue 35
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 PlaceSouvenir 接口的详细说明，如是否返回摆放成功状态。
- 修改建议: 建议在接口说明中补充返回参数，如 placed_flag。
### Issue 36
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 SyncRoomState 接口的详细说明，如是否返回同步时间戳。
- 修改建议: 建议在接口说明中补充返回参数，如 sync_timestamp。
### Issue 37
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 SyncAffectionReward 接口的详细说明，如是否返回主游戏奖励数据。
- 修改建议: 建议在接口说明中补充返回参数，如 main_game_reward_data。
### Issue 38
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 RequestAffectionReset 接口的详细说明，如是否返回重置后的好感度等级。
- 修改建议: 建议在接口说明中补充返回参数，如 new_affection_level。
### Issue 39
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 HeartbeatSync 接口的详细说明，如是否返回同步标志。
- 修改建议: 建议在接口说明中补充返回参数，如 sync_required_flag。
### Issue 40
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 S->C: DLCRefunded 接口的详细说明，如是否返回退款标志。
- 修改建议: 建议在接口说明中补充返回参数，如 dlc_refunded_flag。
### Issue 41
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 S->C: CharacterUnlocked 接口的详细说明，如是否返回角色解锁标志。
- 修改建议: 建议在接口说明中补充返回参数，如 character_unlocked_flag。
### Issue 42
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 核心接口列表
- 问题描述: 程序蓝图中核心接口列表缺少 S->C: SkinUnlocked 接口的详细说明，如是否返回皮肤解锁标志。
- 修改建议: 建议在接口说明中补充返回参数，如 skin_unlocked_flag。
### Issue 43
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 配置表加载流程
- 问题描述: 程序蓝图中配置表加载流程提到读取 system_numerical_data.json，但实际数值配表文件名为 system_numerical_docs.json 和 data.json，存在不一致。
- 修改建议: 建议统一文件名或明确加载哪个文件。
### Issue 44
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“小游戏得分等级奖励：score_grade = {S:100+1碎片, A:80, B:50, C:30}”，但数值配表中 score_grade 定义在 relations_and_enums.enums 中，而程序蓝图未明确引用该枚举。
- 修改建议: 建议在蓝图中明确引用 relations_and_enums.enums.score_grade。
### Issue 45
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“剧情解锁等级要求：story_unlock_affection_level_requirement = [3,5,7,9,10]”，但数值配表中该字段为线性增长公式，生成序列为3,5,7,9,11...，与蓝图不一致。
- 修改建议: 建议统一为离散列表或调整公式。
### Issue 46
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“小游戏解锁等级：minigame_unlock_affection_level = [1,3,6]”，但数值配表中该字段 base 为0，growth 为3，生成序列为0,3,6,9...，与蓝图不一致。
- 修改建议: 建议统一为离散列表或调整公式。
### Issue 47
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“特殊事件触发等级：special_event_trigger_level = [5,8,10]”，但数值配表中该字段 base 为5，growth 为3，生成序列为5,8,11...，与蓝图不一致。
- 修改建议: 建议统一为离散列表或调整公式。
### Issue 48
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“AI行为概率表：behavior_trigger_probability = {看书:0.3, 发呆:0.2, 做家务:0.15, 哼歌:0.1, 玩手机:0.1, 伸懒腰:0.05, 走动:0.1}”，但数值配表中该字段为单一浮点数，无法表示多个概率。
- 修改建议: 建议在蓝图中明确引用 relations_and_enums.enums.current_behavior_id 并补充概率配置。
### Issue 49
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“语音触发概率：voice_trigger_probability = 0.1”，但数值配表中该字段为单一浮点数，而策划案中每个行为可独立配置语音概率。
- 修改建议: 建议在蓝图中明确语音触发概率是全局还是每个行为独立。
### Issue 50
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“拍照模式参数范围：camera_zoom = [0.5, 5.0]”，但数值配表中该字段为线性增长，与范围不匹配。
- 修改建议: 建议在蓝图中明确 camera_zoom 是范围还是步长。
### Issue 51
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“互动热点解锁等级：unlock_affection_level_requirement = 5（如“躺在床上”）”，但数值配表中该字段为线性增长，且策划案中仅举例一个热点。
- 修改建议: 建议在蓝图中明确所有热点的解锁等级配置方式。
### Issue 52
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“房间状态枚举：room_state = [default, level5_upgrade, level8_upgrade, level10_upgrade]”，但数值配表中该枚举定义在 relations_and_enums.enums 中，而蓝图未明确引用。
- 修改建议: 建议在蓝图中明确引用 relations_and_enums.enums.room_state。
### Issue 53
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“行为ID枚举：current_behavior_id = {1:看书, 2:发呆, 3:做家务, 4:哼歌, 5:玩手机, 6:伸懒腰, 7:走动}”，但数值配表中该枚举定义在 relations_and_enums.enums 中，而蓝图未明确引用。
- 修改建议: 建议在蓝图中明确引用 relations_and_enums.enums.current_behavior_id。
### Issue 54
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“滤镜ID枚举：selected_filter_id = {0:无滤镜, 1:清新, 2:复古, 3:黑白, 4:暖色}”，但数值配表中该枚举定义在 relations_and_enums.enums 中，而蓝图未明确引用。
- 修改建议: 建议在蓝图中明确引用 relations_and_enums.enums.selected_filter_id。
### Issue 55
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“姿势ID枚举：selected_pose_id = {0:默认, 1:站立, 2:坐姿, 3:躺姿, 4:依靠}”，但数值配表中该枚举定义在 relations_and_enums.enums 中，而蓝图未明确引用。
- 修改建议: 建议在蓝图中明确引用 relations_and_enums.enums.selected_pose_id。
### Issue 56
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“表情ID枚举：selected_expression_id = {0:默认, 1:微笑, 2:害羞, 3:惊讶, 4:眨眼}”，但数值配表中该枚举定义在 relations_and_enums.enums 中，而蓝图未明确引用。
- 修改建议: 建议在蓝图中明确引用 relations_and_enums.enums.selected_expression_id。
### Issue 57
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“购买平台枚举：purchase_platform = [iOS, Android, PC]”，但数值配表中该枚举定义在 relations_and_enums.enums 中，而蓝图未明确引用。
- 修改建议: 建议在蓝图中明确引用 relations_and_enums.enums.purchase_platform。
### Issue 58
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“超时阈值：房间加载超时=10秒，小游戏加载超时=15秒，剧情加载超时=20秒，玩家闲置超时=5分钟”，但数值配表中未定义这些超时阈值，策划案中仅在边界与异常兜底中提及。
- 修改建议: 建议在数值配表中添加超时阈值字段，或在蓝图中明确为硬编码值。
### Issue 59
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 关键配置挂载点
- 问题描述: 程序蓝图中关键配置挂载点提到“数据同步间隔：5分钟”，但数值配表中未定义该间隔，策划案中在数据联动系统中提及。
- 修改建议: 建议在数值配表中添加数据同步间隔字段，或在蓝图中明确为硬编码值。
**当前审查总计问题:** 59 个

--- 审查时间: 2026-05-28 14:18:52 ---
### Issue 1
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 互动热点系统
- 问题描述: 策划案中互动热点每次触发增加好感度固定值+5点，但数值配表（continuous_formulas）中 interaction_hotspot_system 的 affection_increment 未定义，且数值说明书中 affection_increment 固定为10，与策划案+5矛盾。
- 修改建议: 请确认互动热点每次触发增加的好感度经验值应为5还是10，并确保数值配表与策划案一致。
### Issue 2
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.affection_increment
- 问题描述: 数值说明书中 affection_increment 描述为“每次互动增加的好感度经验值，固定为10”，但策划案中互动热点每次增加+5点，小游戏胜利+20、失败+5，存在冲突。
- 修改建议: 请将 affection_increment 拆分为多个字段（如 hotspot_affection_increment、minigame_win_increment、minigame_lose_increment），或明确该字段仅适用于某一类互动。
### Issue 3
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.daily_play_count
- 问题描述: 数值说明书中 daily_play_count 的默认值为0，取值范围0-3，但策划案中每个小游戏每日可玩5次，且数值配表中 max_daily_play_count 固定为3，与策划案5次矛盾。
- 修改建议: 请统一每日游玩次数为5次（策划案）或3次（数值配表），并同步修改数值说明书中的取值范围。
### Issue 4
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.experience_to_next_level
- 问题描述: 数值说明书中 experience_to_next_level 描述为“计算公式为当前等级*100”，但数值配表中 affection_system 的 experience_to_next_level 的 base=100, growth=100，公式为 100 + (level-1)*100，与描述不一致。
- 修改建议: 请统一升级所需经验公式：若为当前等级*100（1级需100，2级需200...），则配表应为 base=100, growth=100；若为固定100+等级*100，则需修改描述。
### Issue 5
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 小游戏系统
- 问题描述: 策划案中每日可玩5次，但数值配表中 max_daily_play_count 固定为3，且程序蓝图也引用3次，存在三方不一致。
- 修改建议: 请确认每日游玩次数，并同步修改数值配表和程序蓝图中的对应配置。
### Issue 6
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 好感度系统
- 问题描述: 策划案中好感度等级上限为10级，每级所需经验递增（如1级需100经验，10级需5000经验），但数值配表中 experience_to_next_level 为线性增长（base=100, growth=100），无法达到5000经验（10级时仅需1000经验）。
- 修改建议: 请明确每级所需经验的具体数值或公式，确保与数值配表一致。
### Issue 7
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: AI日常行为系统
- 问题描述: 策划案中行为列表包括：看书、发呆、做家务、哼歌、伸懒腰、玩手机、在窗边眺望，共7种行为。但数值说明书枚举中 behavior_id 包含1-8（8为睡觉），且程序蓝图未明确行为数量，存在不一致。
- 修改建议: 请统一行为列表，确认是否包含“睡觉”行为（闲置超时触发），并在所有文档中保持一致。
### Issue 8
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: relations_and_enums.enum_definitions.behavior_id
- 问题描述: 枚举中 behavior_id 包含8种行为（1-8），但策划案中仅列出7种，且缺少“走动”行为的描述（枚举中5为玩手机，6为伸懒腰，7为走动，8为睡觉），与策划案不一致。
- 修改建议: 请与策划对齐行为列表，确保枚举与策划案完全匹配。
### Issue 9
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 五、 数值与配置表挂载
- 问题描述: 程序蓝图中引用小游戏每日次数为3次（max_daily_play_count），但策划案中为5次，且数值配表中也为3次，但策划案是需求源头，需确认。
- 修改建议: 请根据最终确认的每日次数（5次或3次）更新程序蓝图中的配置引用。
### Issue 10
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 五、 数值与配置表挂载
- 问题描述: 程序蓝图中提到“好感度配置：affection_increment（固定10）”，但策划案中互动热点每次+5，小游戏胜利+20、失败+5，固定10与策划案矛盾。
- 修改建议: 请根据策划案细化好感度增量配置，区分不同来源的增量值。
### Issue 11
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 拍照模式
- 问题描述: 策划案中滤镜列表为“清新”、“暖阳”、“复古”、“黑白”共4种，但数值说明书枚举中 filter_id 为1:清新, 2:复古, 3:黑白, 4:暖色，缺少“暖阳”且顺序不同。
- 修改建议: 请统一滤镜名称和顺序，确保策划案与数值说明书一致。
### Issue 12
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: relations_and_enums.enum_definitions.filter_id
- 问题描述: 枚举中滤镜为“清新”、“复古”、“黑白”、“暖色”，但策划案中为“清新”、“暖阳”、“复古”、“黑白”，缺少“暖阳”且多出“暖色”。
- 修改建议: 请与策划对齐滤镜列表，确保枚举与策划案完全匹配。
### Issue 13
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 互动热点系统
- 问题描述: 策划案中每个热点冷却时间为30秒，但数值配表中 cooldown_timer 的 base=30, growth=0，一致。但策划案中未提及冷却时间是否随好感度变化，而数值配表为固定值，需确认是否需动态调整。
- 修改建议: 请明确冷却时间是否受好感度等级影响，若需动态调整，请补充公式。
### Issue 14
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 好感度系统
- 问题描述: 策划案中每日通过互动热点获得的好感度经验有上限200点，但数值配表和程序蓝图中均未定义该上限的配置字段。
- 修改建议: 请在数值配表中增加每日互动好感度上限字段（如 daily_interaction_affection_cap），并在程序蓝图中引用。
### Issue 15
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 三、 后端逻辑划分 (Server)
- 问题描述: 程序蓝图中持久化数据未包含互动热点冷却时间字段（cooldown_timer），但该字段在数值说明书中定义且需要服务端校验。
- 修改建议: 请在持久化数据中增加互动热点冷却时间相关字段，或明确冷却时间仅由客户端管理。
### Issue 16
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 纪念品系统
- 问题描述: 策划案中纪念品解锁条件包括好感度6级和小游戏成就，但数值说明书中 souvenir_fragment_count 与 minigame_system 联动，策划案未提及碎片合成机制，存在逻辑缺失。
- 修改建议: 请补充纪念品碎片合成机制或移除碎片相关字段，确保策划案与数值说明书一致。
### Issue 17
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary.souvenir_fragment_count
- 问题描述: 数值说明书中 souvenir_fragment_count 描述为“纪念品碎片数量”，但策划案中纪念品为直接解锁，无碎片合成机制，存在功能不匹配。
- 修改建议: 请与策划确认纪念品解锁方式，若为直接解锁则移除碎片相关字段，若为碎片合成则需在策划案中补充。
**当前审查总计问题:** 17 个
