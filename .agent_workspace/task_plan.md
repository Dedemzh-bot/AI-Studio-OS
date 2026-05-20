# 角色私人宿舍系统 - WBS 任务拆解计划

## 1. 任务分解

### System Planner (系统策划)
- **任务1.1**: 细化互动部位定义与反馈映射表
  - 输入: 设计草案 (Section 二、三)
  - 产出: `interaction_zones.md` - 包含部位列表、触发条件、反馈类型(语音/动作/表情)、敏感度等级
- **任务1.2**: 设计小游戏规则与触发逻辑
  - 输入: 设计草案 (Section 二.3)
  - 产出: `minigame_rules.md` - 包含小游戏类型、胜负条件、好感度增减规则、触发概率机制
- **任务1.3**: 定义宿舍商店与道具系统
  - 输入: 设计草案 (Section 四)
  - 产出: `dorm_shop_design.md` - 包含商品列表、价格、解锁条件、道具效果

### Numerical Planner (数值策划)
- **任务2.1**: 设计好感度增长曲线
  - 输入: `interaction_zones.md`, `minigame_rules.md`
  - 产出: `affection_growth.xlsx` - 每次互动/小游戏胜利的好感度增加值，等级解锁阈值
- **任务2.2**: 设计宿舍币与宿舍券经济模型
  - 输入: 设计草案 (Section 四)
  - 产出: `dorm_economy.xlsx` - 宿舍币产出/消耗表，宿舍券每日获取/付费定价
- **任务2.3**: 设计小游戏触发概率配置
  - 输入: `minigame_rules.md`
  - 产出: `minigame_probability.xlsx` - 基础概率、疲劳衰减系数、付费加成

### Schema Translator (格式翻译)
- **任务3.1**: 翻译互动部位配置为 JSON Schema
  - 输入: `interaction_zones.md`
  - 产出: `interaction_zones_schema.json`
- **任务3.2**: 翻译小游戏规则为 JSON Schema
  - 输入: `minigame_rules.md`
  - 产出: `minigame_rules_schema.json`
- **任务3.3**: 翻译宿舍商店配置为 JSON Schema
  - 输入: `dorm_shop_design.md`
  - 产出: `dorm_shop_schema.json`
- **任务3.4**: 翻译经济模型为 JSON Schema
  - 输入: `dorm_economy.xlsx`
  - 产出: `dorm_economy_schema.json`

### Code Agent (程序执行)
- **任务4.1**: 实现触摸互动系统
  - 输入: `interaction_zones_schema.json`
  - 产出: `touch_interaction.gd` - 触摸检测、反馈触发、疲劳逻辑
- **任务4.2**: 实现小游戏系统
  - 输入: `minigame_rules_schema.json`
  - 产出: `minigame_system.gd` - 小游戏管理器、具体游戏逻辑
- **任务4.3**: 实现宿舍商店系统
  - 输入: `dorm_shop_schema.json`
  - 产出: `dorm_shop.gd` - 商品展示、购买逻辑、道具使用
- **任务4.4**: 实现经济系统集成
  - 输入: `dorm_economy_schema.json`
  - 产出: `dorm_economy.gd` - 货币增减、道具消耗、接口对接
- **任务4.5**: 实现旧系统数据联动
  - 输入: 设计草案 (Section 五)
  - 产出: `legacy_integration.gd` - 好感度接口调用、模型加载、语音播放

### UI Agent (UX/UI 设计)
- **任务5.1**: 设计宿舍主界面 UI
  - 输入: 设计草案 (Section 三)
  - 产出: `dorm_main_ui.md` - 包含布局、按钮、图标、颜色方案
- **任务5.2**: 设计互动反馈 UI 元素
  - 输入: `interaction_zones.md`
  - 产出: `interaction_feedback_ui.md` - 触摸高亮、表情气泡、好感度进度条
- **任务5.3**: 设计小游戏 UI
  - 输入: `minigame_rules.md`
  - 产出: `minigame_ui.md` - 游戏界面、计分板、结果展示
- **任务5.4**: 设计宿舍商店 UI
  - 输入: `dorm_shop_design.md`
  - 产出: `dorm_shop_ui.md` - 商品列表、购买弹窗、预览功能

### Audit Agent (审查官)
- **任务6.1**: 审查互动部位配置
  - 输入: `interaction_zones_schema.json`
  - 产出: `audit_interaction_zones.md` - 通过/驳回，含极端情况检测
- **任务6.2**: 审查小游戏规则
  - 输入: `minigame_rules_schema.json`
  - 产出: `audit_minigame_rules.md` - 通过/驳回，含概率平衡检测
- **任务6.3**: 审查经济模型
  - 输入: `dorm_economy_schema.json`
  - 产出: `audit_dorm_economy.md` - 通过/驳回，含通货膨胀检测

### Combat Agent (战斗策划)
- **任务7.1**: 设计互动语音与动作触发数值
  - 输入: `interaction_zones.md`
  - 产出: `interaction_combat_values.json` - 语音ID、动作ID、触发权重
- **任务7.2**: 设计小游戏胜负因果链
  - 输入: `minigame_rules.md`
  - 产出: `minigame_combat_values.json` - 胜负概率、奖励倍率、疲劳累积

## 2. 执行顺序与依赖

### 串行依赖链
```
Phase 1: 基础设计
  System Planner (1.1, 1.2, 1.3) → 并行
  ↓
Phase 2: 数值与格式
  Numerical Planner (2.1, 2.2, 2.3) → 并行
  Schema Translator (3.1, 3.2, 3.3, 3.4) → 并行
  ↓
Phase 3: 审查与开发
  Audit Agent (6.1, 6.2, 6.3) → 并行 (依赖 Phase 2 产出)
  Combat Agent (7.1, 7.2) → 并行 (依赖 Phase 1 产出)
  ↓
Phase 4: 实现与UI
  Code Agent (4.1, 4.2, 4.3, 4.4, 4.5) → 并行 (依赖 Phase 3 通过)
  UI Agent (5.1, 5.2, 5.3, 5.4) → 并行 (依赖 Phase 1 产出)
```

### 可并行任务
- **Phase 1 内部**: System Planner 的三个任务完全独立
- **Phase 2 内部**: Numerical Planner 与 Schema Translator 可并行
- **Phase 3 内部**: Audit Agent 与 Combat Agent 可并行
- **Phase 4 内部**: Code Agent 与 UI Agent 可并行

### 关键依赖点
- **Code Agent 必须等待 Audit Agent 通过**，否则可能返工
- **UI Agent 可提前基于设计草案开始**，但最终需与 Code Agent 对齐

## 3. 风险提示

### 阻塞点
1. **旧系统接口不兼容**: 好感度、模型、语音系统可能缺少必要接口，需提前确认 API 文档
2. **3D模型精度问题**: 宿舍模型需更高精度，可能超出当前渲染管线能力，需评估性能
3. **语音资源不足**: ASMR 级别语音录制周期长，可能成为关键路径瓶颈

### 跨团队依赖冲突
1. **System Planner vs. Numerical Planner**: 互动部位定义可能影响好感度增长曲线设计，需同步迭代
2. **Combat Agent vs. Code Agent**: 语音/动作 ID 映射需与程序实现一致，避免硬编码
3. **UI Agent vs. Code Agent**: UI 布局需与触摸检测区域对齐，否则交互失效

### 其他风险
- **小游戏概率平衡**: 付费加成可能破坏免费玩家体验，需 Audit Agent 严格审查
- **擦边红线**: 所有互动设计需经法务确认，避免违规下架
- **性能优化**: 物理抖动和材质表现可能影响低端设备帧率，需预留优化时间