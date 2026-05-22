
--- 审查时间: 2026-05-22 16:49:33 ---
### Issue 1
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 二、核心规则与玩法机制 - 2.1 参与条件
- 问题描述: 策划案中明确要求玩家需拥有至少一名五星角色才能解锁宿舍，但数值说明书和配表中均未定义如何校验玩家是否拥有五星角色，也未定义对应的接口或字段。
- 修改建议: 建议在数值说明书的 field_dictionary 中增加一个字段（如 has_five_star_role）或明确说明复用已有接口 get_owned_five_star_roles 的校验逻辑，并在配表中补充该条件的判断规则。
### Issue 2
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 二、核心规则与玩法机制 - 2.2 玩法循环 - 互动模式
- 问题描述: 策划案中提到互动冷却时间为5秒，但未明确该冷却时间是针对单个角色还是全局所有角色。数值配表中 interaction_cooldown 的默认值为5.0，但未区分作用域。
- 修改建议: 建议在策划案中明确冷却时间的作用域（如每个角色独立冷却），并在数值说明书中增加字段说明冷却时间的作用范围。
### Issue 3
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary - dormitory_affection
- 问题描述: 数值说明书中定义 dormitory_affection 的范围为0-1000，但配表中 get_dormitory_affection 的离散里程碑只列出了0, 50, 120, 210, 320, 450, 600, 770, 960, 1000，缺少中间值的处理逻辑（如如何计算等级）。
- 修改建议: 建议在配表中增加一个等级计算表或说明，明确每个好感度值对应的等级（如0-49为Lv.1，50-119为Lv.2等），或者直接使用 implementation_notes 中的阈值数组。
### Issue 4
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary - add_dormitory_affection
- 问题描述: 数值说明书中定义 add_dormitory_affection 的范围为1-50，但配表中 add_dormitory_affection 的离散里程碑只列出了 interaction:1, minigame_win:50, minigame_lose:10，缺少其他互动场景（如禁区点击）的好感度增加值。
- 修改建议: 建议在配表中补充禁区点击的好感度增加值（策划案中明确无奖励，应设为0），并明确是否还有其他互动场景的好感度增加值。
### Issue 5
- 责任方: numerical_planner
- 目标文件: system_numerical_docs.json
- 锚点: field_dictionary - minigame_weekly_reset
- 问题描述: 数值说明书中定义 minigame_weekly_reset 为布尔型，但配表中将其作为离散里程碑处理（0: false, 1: true），与策划案中“每周一重置”的逻辑不一致。配表应体现时间重置逻辑而非简单的布尔值。
- 修改建议: 建议将 minigame_weekly_reset 改为时间戳字段，记录上次重置时间，或明确说明该字段由服务端根据当前时间动态计算，而非存储布尔值。
### Issue 6
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 三、后端逻辑划分 (Server) - 1. 持久化数据 (DB) - player_dormitory_affection 表
- 问题描述: 程序蓝图中 player_dormitory_affection 表存储了 unlocked_interactions 和 unlocked_voice_lines 的JSON数组，但策划案和数值说明书中均未定义这些字段的存储逻辑。这些数据应通过好感度等级动态计算，而非持久化存储。
- 修改建议: 建议移除 player_dormitory_affection 表中的 unlocked_interactions 和 unlocked_voice_lines 字段，改为在 get_dormitory_interaction_list 接口中根据当前好感度值动态计算返回。
### Issue 7
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、前后端通信协议 (API & 数据对接) - add_dormitory_affection 接口
- 问题描述: 程序蓝图中 add_dormitory_affection 接口的返回参数包含 unlocked_items，但数值配表中 add_dormitory_affection 的离散里程碑并未定义解锁物品的返回逻辑。接口设计超前于数值配置。
- 修改建议: 建议在数值配表中增加 add_dormitory_affection 接口返回的 unlocked_items 字段定义，或由服务端在返回时动态计算新解锁的物品。
### Issue 8
- 责任方: tech_architect
- 目标文件: tech_blueprint.md
- 锚点: 四、前后端通信协议 (API & 数据对接) - minigame_submit_action 接口
- 问题描述: 程序蓝图中 minigame_submit_action 接口的请求参数包含 round 和 action，但策划案和数值说明书中均未定义小游戏的具体回合数和动作类型。接口设计缺乏上游文档支持。
- 修改建议: 建议在策划案中补充小游戏的具体规则（如猜拳的回合数、动作枚举值），并在数值说明书中定义 action 的枚举值（如 rock, paper, scissors）。
### Issue 9
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 五、旧系统与数据联动 - 5.2 需新增的全局接口
- 问题描述: 策划案中列出了 is_dormitory_unlocked 和 get_dormitory_interaction_list 两个接口，但程序蓝图中的 API 列表还包含了 unlock_dormitory、get_owned_five_star_roles、get_dormitory_affection、add_dormitory_affection、get_unlocked_skins、minigame_start、minigame_submit_action、minigame_end、get_dormitory_voice_pool 等接口。策划案未完整定义所有必要接口。
- 修改建议: 建议在策划案中补充所有必要的接口定义，包括解锁、好感度操作、小游戏相关接口，确保与程序蓝图一致。
### Issue 10
- 责任方: system_planner
- 目标文件: system_design_detail.md
- 锚点: 三、表现层与角色展示联动 - 3.2 擦边互动设计
- 问题描述: 策划案中明确互动区域限制为头部、肩膀、手臂、腰部、手部，但数值配表和程序蓝图中均未定义如何配置这些互动区域。程序蓝图提到需要独立的 interaction_zone_config.json，但策划案未提供该配置文件的定义。
- 修改建议: 建议在策划案中补充互动区域配置文件的定义，包括每个角色的骨骼名称与互动区域类型的映射关系。
**当前审查总计问题:** 10 个
