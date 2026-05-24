# 项目记忆 Codex

> 仅扫描业务数据表，已过滤框架文件、外键字段。
> ID 已做范围压缩 / 去重截断，防止 Token 爆炸。
> 主键/外键已严格区分：只记录本模块主键 ID。

## 系统概览
- 已有系统模块: affection_growth_and_unlock_system, character_room_loading_and_initialization, core_interaction_dialogue_system, core_interaction_touch_feedback_system, costume_display_and_skin_linkage, economy_cycle_and_monetization, room_customization_and_furniture_system, system_core_entry_and_unlock

## 已占用的主键 ID（范围压缩 / 去重截断）
- 共 3 组
  - `[system_numerical_data] action_id: action_chest_shrink, action_face_touch, action_hand_hold ...等 5 个`
  - `[system_numerical_data] expression_id: expr_blush, expr_blush_deep, expr_happy ...等 5 个`
  - `[system_numerical_data] voice_id: voice_chest_01, voice_face_01, voice_hand_01 ...等 5 个`

## 业务数据表清单
- **.retry_count.json** (0.0 KB) | 顶级 Key: `agent, count`
- **system_numerical_data.json** (4.6 KB) | 顶级 Key: `continuous_formulas, discrete_milestones` | 主键: [system_numerical_data] voice_id: voice_chest_01, voice_face_01, voice_hand_01 ...等 5 个, [system_numerical_data] expression_id: expr_blush, expr_blush_deep, expr_happy ...等 5 个, [system_numerical_data] action_id: action_chest_shrink, action_face_touch, action_hand_hold ...等 5 个
- **system_numerical_docs.json** (9.2 KB) | 顶级 Key: `system_summary, field_dictionary, relations_and_enums, implementation_notes`
- **system_schema.json** (2.7 KB) | 模块: affection_growth_and_unlock_system, character_room_loading_and_initialization, core_interaction_dialogue_system, core_interaction_touch_feedback_system, costume_display_and_skin_linkage, economy_cycle_and_monetization, room_customization_and_furniture_system, system_core_entry_and_unlock
