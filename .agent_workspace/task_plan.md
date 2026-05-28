# 角色私人宿舍 - WBS 任务拆解计划

## 1. 任务分解

### System Planner (系统策划)
- **任务1.1：系统闭环与模块边界定义**
  - 输入：`角色私人宿舍 - 宏观设计草案.md`
  - 产出：`宿舍系统模块边界.md`（明确各子系统间的数据流、状态机、触发条件）
- **任务1.2：互动热点与好感度成长曲线框架**
  - 输入：`宿舍系统模块边界.md`
  - 产出：`互动热点配置表框架.md`（热点类型、触发条件、动画ID、好感度奖励值）
- **任务1.3：小游戏系统框架设计**
  - 输入：`宿舍系统模块边界.md`
  - 产出：`小游戏系统框架.md`（每个角色的2-3个小游戏玩法描述、胜负条件、奖励规则）
- **任务1.4：AI日常行为逻辑设计**
  - 输入：`宿舍系统模块边界.md`
  - 产出：`AI行为状态机.md`（行为列表、触发概率、切换条件、动画ID映射）
- **任务1.5：拍照模式功能定义**
  - 输入：`宿舍系统模块边界.md`
  - 产出：`拍照模式功能规格.md`（视角控制、滤镜参数、姿势/表情切换逻辑）

### Numerical Planner (数值策划)
- **任务2.1：好感度数值曲线设计**
  - 输入：`互动热点配置表框架.md`
  - 产出：`好感度成长曲线.xlsx`（每级所需经验、互动/小游戏单次奖励值、解锁阈值）
- **任务2.2：小游戏数值平衡**
  - 输入：`小游戏系统框架.md`
  - 产出：`小游戏数值表.xlsx`（每个小游戏的难度曲线、得分规则、奖励倍率）
- **任务2.3：纪念品解锁条件数值化**
  - 输入：`小游戏系统框架.md`
  - 产出：`纪念品解锁条件表.xlsx`（每个纪念品对应的成就/挑战完成次数、好感度等级要求）

### Schema Translator (格式翻译)
- **任务3.1：好感度系统 JSON Schema**
  - 输入：`好感度成长曲线.xlsx`
  - 产出：`affection_system_schema.json`
- **任务3.2：互动热点系统 JSON Schema**
  - 输入：`互动热点配置表框架.md`
  - 产出：`interaction_hotspot_schema.json`
- **任务3.3：小游戏系统 JSON Schema**
  - 输入：`小游戏数值表.xlsx`
  - 产出：`minigame_system_schema.json`
- **任务3.4：AI行为系统 JSON Schema**
  - 输入：`AI行为状态机.md`
  - 产出：`ai_behavior_schema.json`
- **任务3.5：纪念品系统 JSON Schema**
  - 输入：`纪念品解锁条件表.xlsx`
  - 产出：`souvenir_system_schema.json`
- **任务3.6：拍照模式 JSON Schema**
  - 输入：`拍照模式功能规格.md`
  - 产出：`photo_mode_schema.json`

### Combat Agent (战斗策划)
- **任务4.1：角色模型精度与物理参数配置**
  - 输入：`角色私人宿舍 - 宏观设计草案.md`（表现层要求）
  - 产出：`character_model_config.json`（模型LOD等级、Jiggle Physics参数、面部表情BlendShape映射）
- **任务4.2：互动动画触发逻辑配置**
  - 输入：`互动热点配置表框架.md`
  - 产出：`interaction_animation_config.json`（每个热点对应的动画ID、运镜参数、物理反馈开关）

### UI Agent (UX/UI 设计)
- **任务5.1：宿舍主界面UI设计**
  - 输入：`宿舍系统模块边界.md`
  - 产出：`dormitory_ui_design.md`（角色选择界面、房间切换、UI最小化方案）
- **任务5.2：互动UI设计**
  - 输入：`互动热点配置表框架.md`
  - 产出：`interaction_ui_design.md`（热点提示、好感度气泡、手机消息式UI）
- **任务5.3：拍照模式UI设计**
  - 输入：`拍照模式功能规格.md`
  - 产出：`photo_mode_ui_design.md`（滤镜选择、姿势切换、截图按钮布局）
- **任务5.4：小游戏UI设计**
  - 输入：`小游戏系统框架.md`
  - 产出：`minigame_ui_design.md`（每个小游戏的HUD、计分板、操作提示）

### Code Agent (程序执行)
- **任务6.1：好感度系统代码实现**
  - 输入：`affection_system_schema.json`
  - 产出：`affection_system.gd`
- **任务6.2：互动热点系统代码实现**
  - 输入：`interaction_hotspot_schema.json`
  - 产出：`interaction_hotspot.gd`
- **任务6.3：小游戏系统代码实现**
  - 输入：`minigame_system_schema.json`
  - 产出：`minigame_system.gd`
- **任务6.4：AI行为系统代码实现**
  - 输入：`ai_behavior_schema.json`
  - 产出：`ai_behavior.gd`
- **任务6.5：纪念品系统代码实现**
  - 输入：`souvenir_system_schema.json`
  - 产出：`souvenir_system.gd`
- **任务6.6：拍照模式代码实现**
  - 输入：`photo_mode_schema.json`
  - 产出：`photo_mode.gd`
- **任务6.7：角色模型与物理系统集成**
  - 输入：`character_model_config.json`
  - 产出：`character_model_integration.gd`
- **任务6.8：互动动画触发代码实现**
  - 输入：`interaction_animation_config.json`
  - 产出：`interaction_animation.gd`

### Audit Agent (审查官)
- **任务7.1：好感度数值平衡审查**
  - 输入：`好感度成长曲线.xlsx`
  - 产出：`affection_balance_audit.md`（审查意见、调整建议）
- **任务7.2：小游戏数值平衡审查**
  - 输入：`小游戏数值表.xlsx`
  - 产出：`minigame_balance_audit.md`（审查意见、调整建议）
- **任务7.3：整体经济循环审查**
  - 输入：`好感度成长曲线.xlsx`、`小游戏数值表.xlsx`、`纪念品解锁条件表.xlsx`
  - 产出：`economy_cycle_audit.md`（确认无内购、无货币产出/消耗、纯内容解锁）

## 2. 执行顺序与依赖

### 串行路径（必须按顺序执行）
```
Phase 1: 系统设计
  System Planner (1.1) → System Planner (1.2, 1.3, 1.4, 1.5) [可并行]

Phase 2: 数值与格式
  Numerical Planner (2.1, 2.2, 2.3) [可并行]
  ↓
  Schema Translator (3.1, 3.2, 3.3, 3.4, 3.5, 3.6) [可并行]
  ↓
  Audit Agent (7.1, 7.2, 7.3) [可并行]

Phase 3: 战斗与UI设计（可与Phase 2并行）
  Combat Agent (4.1, 4.2) [可并行]
  UI Agent (5.1, 5.2, 5.3, 5.4) [可并行]

Phase 4: 代码实现（依赖Phase 2和Phase 3完成）
  Code Agent (6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8) [可并行]
```

### 并行任务组
- **组A（设计阶段）：** System Planner 所有任务（1.1-1.5）
- **组B（数值与格式阶段）：** Numerical Planner 所有任务（2.1-2.3）→ Schema Translator 所有任务（3.1-3.6）→ Audit Agent 所有任务（7.1-7.3）
- **组C（战斗与UI阶段）：** Combat Agent 所有任务（4.1-4.2）+ UI Agent 所有任务（5.1-5.4）
- **组D（代码阶段）：** Code Agent 所有任务（6.1-6.8）

### 依赖关系图
```
1.1 → 1.2, 1.3, 1.4, 1.5
1.2 → 2.1, 2.2, 2.3
1.3 → 2.2, 2.3
1.4 → 3.4
1.5 → 3.6
2.1 → 3.1, 7.1
2.2 → 3.3, 7.2
2.3 → 3.5, 7.3
3.1 → 6.1
3.2 → 6.2
3.3 → 6.3
3.4 → 6.4
3.5 → 6.5
3.6 → 6.6
4.1 → 6.7
4.2 → 6.8
5.1 → 6.1 (UI集成)
5.2 → 6.2 (UI集成)
5.3 → 6.6 (UI集成)
5.4 → 6.3 (UI集成)
7.1, 7.2, 7.3 → 6.1, 6.3, 6.5 (审查通过后代码实现)
```

## 3. 风险提示

### 阻塞点
1. **System Planner 1.1 是全局阻塞点**：模块边界定义未完成前，所有下游任务无法启动。需确保1.1产出包含清晰的子系统数据流、状态机、触发条件。
2. **Audit Agent 审查阻塞**：数值平衡审查（7.1-7.3）未通过前，Code Agent 不能开始实现对应模块。需预留审查迭代时间。
3. **Combat Agent 4.1 模型配置阻塞**：角色模型精度与物理参数配置未完成前，Code Agent 6.7 无法集成。需与美术团队提前对齐模型LOD等级和物理参数范围。

### 跨团队依赖冲突
1. **UI Agent 与 Code Agent 的UI集成**：UI设计（5.1-5.4）需与Code Agent（6.1-6.6）紧密协作，确保UI元素正确绑定到游戏逻辑。建议UI Agent产出包含明确的UI组件ID和事件绑定规范。
2. **Combat Agent 与 System Planner 的动画ID映射**：互动动画配置（4.2）依赖System Planner的互动热点设计（1.2）。需确保两者使用相同的动画ID命名规范。
3. **Numerical Planner 与 Schema Translator 的数值格式**：数值表（2.1-2.3）的Excel格式需与Schema Translator的JSON Schema字段完全对齐。建议提前定义字段映射模板。

### 其他风险
1. **内容量风险**：纯买断制下，每个角色需制作2-3个小游戏和大量互动动画。Code Agent 6.3 和 6.8 的工作量可能被低估，需评估是否需拆分多个子任务或增加人力。
2. **技术性能风险**：高精度模型与Jiggle Physics对移动端性能压力大。Combat Agent 4.1 需明确LOD切换策略和物理模拟精度等级，Code Agent 6.7 需实现性能监控和降级方案。
3. **好感度联动风险**：宿舍好感度与主游戏头像框/名片背景的联动（弱联动）可能涉及跨系统数据同步。需在System Planner 1.1中明确数据同步接口和触发条件，避免Code Agent实现时出现数据不一致。