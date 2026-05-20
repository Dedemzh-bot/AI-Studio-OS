# 项目记忆 Codex

> 仅扫描业务数据表，已过滤框架文件、外键字段。
> ID 已做范围压缩 / 去重截断，防止 Token 爆炸。
> 主键/外键已严格区分：只记录本模块主键 ID。

## 系统概览
- 已有系统模块: achievement, action_trigger, affection, dormitory_loading, dormitory_purchase, furniture, interaction_detection, minigame

## 已占用的主键 ID（范围压缩 / 去重截断）
- 共 4 组
  - `[achievement] achievement_id: 1 ~ 3`
  - `[dormitory_loading] dormitory_id: 1 ~ 3`
  - `[furniture] furniture_id: 1 ~ 3`
  - `[minigame] minigame_id: 1 ~ 3`

## 业务数据表清单
- **system_numerical_data.json** (5.3 KB) | 顶级 Key: `dormitory_purchase, dormitory_loading, interaction_detection, action_trigger, minigame, affection, achievement, furniture` | 主键: [dormitory_loading] dormitory_id: 1 ~ 3, [minigame] minigame_id: 1 ~ 3, [achievement] achievement_id: 1 ~ 3, [furniture] furniture_id: 1 ~ 3
- **system_numerical_docs.json** (5.0 KB) | 顶级 Key: `system_summary, field_dictionary, relations_and_enums, implementation_notes`
- **system_schema.json** (2.7 KB) | 模块: achievement, action_trigger, affection, dormitory_loading, dormitory_purchase, furniture, interaction_detection, minigame
