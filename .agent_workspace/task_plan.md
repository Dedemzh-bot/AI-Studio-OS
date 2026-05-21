# 角色私人宿舍系统 - WBS 任务拆解计划

## 1. 任务分解

### System Planner (系统策划)
- **任务**: 细化系统架构与模块划分
- **输入文件**: `终审设计草案.md`
- **产出文件**: 
  - `dorm_system_design.md` - 系统架构文档（含模块划分、交互流程、状态机）
  - `dorm_interaction_matrix.md` - 角色交互矩阵（部位×反应类型×语音ID映射）
  - `dorm_scene_layout.md` - 场景布局规范（镜头参数、UI锚点、碰撞体定义）
- **关键约束**: 所有角色动作独立制作，无通用模板；画质自动分级无自定义入口

### Numerical Planner (数值策划)
- **任务**: 生成付费道具数值表与画质分级配置
- **输入文件**: `dorm_system_design.md`, `终审设计草案.md`
- **产出文件**:
  - `dorm_economy_table.xlsx` - 付费道具定价表（家具/姿势/服装/小游戏）
  - `device_quality_preset.json` - 设备画质分级表（型号→画质等级/物理开关/LOD）
  - `affection_bonus_config.json` - 每日好感度奖励配置
- **边界**: 不改变系统结构，仅填表

### Schema Translator (格式翻译)
- **任务**: 将MD草案翻译为结构化JSON Schema
- **输入文件**: `dorm_system_design.md`, `dorm_interaction_matrix.md`, `dorm_scene_layout.md`
- **产出文件**:
  - `dorm_system_schema.json` - 系统主Schema（含场景、交互、UI配置）
  - `dorm_data_tables_schema.json` - 数据表Schema（家具/姿势/服装/小游戏/画质）
  - `dorm_api_schema.json` - 接口Schema（角色数据/好感度/拍照/短信）
- **边界**: 不改任何业务内容

### Code Agent (程序执行)
- **任务**: 将JSON Schema翻译为GDScript代码
- **输入文件**: `dorm_system_schema.json`, `dorm_data_tables_schema.json`, `dorm_api_schema.json`
- **产出文件**:
  - `dorm_main.gd` - 宿舍主场景控制器
  - `dorm_interaction.gd` - 交互系统（触摸检测、反馈触发）
  - `dorm_camera.gd` - 镜头系统（自由视角/特写切换）
  - `dorm_physics.gd` - 物理系统（软体/布料模拟）
  - `dorm_quality_manager.gd` - 画质自动分级管理器
  - `dorm_minigame_*.gd` - 各小游戏逻辑脚本
  - `dorm_photo_mode.gd` - 拍照模式控制器
- **边界**: 不修改设计意图，只做机械翻译

### UI Agent (UX/UI 设计)
- **任务**: 设计宿舍前端UI配置
- **输入文件**: `dorm_system_design.md`, `dorm_scene_layout.md`
- **产出文件**:
  - `dorm_ui_config.json` - UI配置（半透明浮动按钮、锚点、颜色、图标路径）
  - `dorm_photo_filter_config.json` - 拍照滤镜配置（颜色矩阵、预设参数）
  - `dorm_icon_assets/` - 图标资源（按钮图标、道具图标）
- **边界**: 不涉及引擎动效

### Audit Agent (审查官)
- **任务**: 数值平衡性与合规性审查
- **输入文件**: `dorm_economy_table.xlsx`, `device_quality_preset.json`, `dorm_interaction_matrix.md`
- **产出文件**: `audit_report.md` - 审查报告（通过/驳回+问题列表）
- **审查重点**:
  - 付费定价合理性（6/12/30美元梯度是否合理）
  - 画质分级是否覆盖主流设备
  - 交互内容是否符合底线（无脱衣/露点/性行为模拟）
- **边界**: 只审查不修改

### Combat Agent (战斗策划)
- **任务**: 设计小游戏数值与逻辑
- **输入文件**: `终审设计草案.md`, `dorm_system_design.md`
- **产出文件**:
  - `minigame_config.json` - 小游戏配置（猜拳/拍手/喂食的规则、判定逻辑、奖励）
  - `minigame_animation_trigger.json` - 小游戏胜利/失败动画触发配置
- **边界**: 不写引擎代码

## 2. 执行顺序与依赖

### 串行依赖链（必须按顺序执行）
```
Phase 1: System Planner → 产出设计文档
    ↓
Phase 2: Schema Translator → 产出JSON Schema
    ↓
Phase 3: Code Agent + UI Agent + Combat Agent → 并行产出代码/UI/小游戏配置
    ↓
Phase 4: Numerical Planner → 产出数值表（依赖Phase 1的设计约束）
    ↓
Phase 5: Audit Agent → 审查所有产出
```

### 并行任务（可同时进行）
- **Phase 3 内部并行**:
  - Code Agent 内部可并行：场景控制器、交互系统、镜头系统、物理系统、画质管理器、小游戏脚本、拍照模式
  - UI Agent 与 Combat Agent 可并行
- **Phase 2 与 Phase 4 可部分并行**:
  - Schema Translator 产出数据表Schema后，Numerical Planner 即可开始填表（无需等待完整Schema）

### 关键依赖关系
| 任务 | 依赖 | 产出供谁使用 |
|------|------|-------------|
| System Planner | 无 | Schema Translator, Numerical Planner, UI Agent, Combat Agent |
| Schema Translator | System Planner | Code Agent, UI Agent |
| Numerical Planner | System Planner | Audit Agent |
| Code Agent | Schema Translator | 无（最终产出） |
| UI Agent | System Planner, Schema Translator | 无（最终产出） |
| Combat Agent | System Planner | Code Agent（小游戏逻辑脚本） |
| Audit Agent | Numerical Planner, Schema Translator, UI Agent, Combat Agent | 无（最终审查） |

## 3. 风险提示

### 阻塞点
1. **角色动作独立性导致内容生产瓶颈**
   - 风险：每个角色需独立制作触摸反馈动画（5部位×3反应）、语音（15+条）、专属互动动画。若角色数量>30，独立制作成本极高，可能拖慢整体进度。
   - 建议：在Phase 1中由System Planner明确“独立制作”的具体粒度（如：基础触摸动画可复用模板，仅表情/语音差异化），否则后续Agent无法执行。

2. **画质自动分级策略的边界模糊**
   - 风险：设计草案要求“无玩家自定义入口”，但未定义“设备型号→画质等级”的映射规则。若Numerical Planner无法获取完整设备数据库，可能导致中低端机型体验崩溃。
   - 建议：System Planner需在Phase 1中明确画质分级策略（如：按GPU型号/内存大小/屏幕分辨率分级），并提供默认回退方案。

3. **物理引擎与移动端性能冲突**
   - 风险：软体物理（胸部/臀部抖动）和布料物理（裙摆飘动）在移动端可能严重掉帧。Code Agent需实现物理开关逻辑，但UI Agent无法控制引擎动效。
   - 建议：System Planner需定义“物理效果分级”规则（如：高画质开启全部物理，中画质仅开启布料，低画质关闭所有物理），并明确物理开关的触发时机（加载时检测画质等级）。

### 跨团队依赖冲突
1. **UI Agent 与 Code Agent 的锚点定义冲突**
   - 风险：UI Agent设计的半透明浮动按钮锚点（如：右上角拍照按钮）可能与Code Agent的镜头系统（特写镜头时UI自动隐藏）产生位置冲突。
   - 解决：System Planner需在Phase 1中定义UI层级规范（如：UI始终在相机渲染层之上，特写镜头时UI透明度降至0.2）。

2. **Combat Agent 与 Code Agent 的小游戏逻辑接口不一致**
   - 风险：Combat Agent产出的小游戏配置（如猜拳的胜负判定逻辑）可能未定义Code Agent所需的输入/输出接口（如：玩家选择→AI选择→结果判定→动画触发）。
   - 解决：System Planner需在Phase 1中定义小游戏通用接口规范（输入：玩家操作ID；输出：结果状态+动画ID）。

3. **Numerical Planner 与 Audit Agent 的定价审查标准不一致**
   - 风险：Numerical Planner按草案定价（6/12/30美元），但Audit Agent可能认为定价梯度不合理（如：6美元与12美元差距过大）。
   - 解决：System Planner需在Phase 1中明确定价策略依据（如：参考同类游戏定价、用户付费意愿调研），供Audit Agent审查时参考。

### 其他风险
- **短信系统接口依赖**：购买后感谢短信需调用`message_system`，但该接口可能尚未开发完成。建议Code Agent实现时增加“短信发送失败”的回退方案（如：仅显示UI提示）。
- **拍照系统截图功能**：需新增全局截图功能（隐藏UI、滤镜叠加、分辨率选择），可能涉及引擎底层修改。建议Code Agent优先实现基础截图，滤镜和分辨率选择作为后续迭代。