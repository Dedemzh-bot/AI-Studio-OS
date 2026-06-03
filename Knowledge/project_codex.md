# 项目记忆 Codex

> 仅扫描业务数据表，已过滤框架文件、外键字段。
> ID 已做范围压缩 / 去重截断，防止 Token 爆炸。
> 主键/外键已严格区分：只记录本模块主键 ID。

## 系统概览
- 已有系统模块: UI透明化, 付费埋点, 免费产出, 商城系统联动, 图鉴系统联动, 场景布置, 场景模板切换, 姿势系统, 拍照模式, 换装系统, 擦边底线, 方案保存与切换, 活动系统联动, 物理反馈, 画质分级系统联动, 表情系统, 角色获取系统联动, 角色选择与场景加载, 资源循环, 运镜设计

## 已占用的主键 ID（范围压缩 / 去重截断）
- 共 4 组
  - `[base_expressions] expression_id: blink_01, smile_01`
  - `[base_poses] pose_id: sit_01, stand_01`
  - `[free_filters] filter_id: cool_01, natural_01, soft_01 ...等 5 个`
  - `[scene_templates] template_id: balcony_01, bedroom_01, garden_01 ...等 5 个`

## 业务数据表清单
- **.web_prompt.json** (0.1 KB) | 顶级 Key: `prompt, ts, answered`
- **project_meta.json** (0.1 KB) | 顶级 Key: `system_name, primary_tag, version`
- **system_numerical_data.json** (2.6 KB) | 顶级 Key: `global_parameters, scene_templates, base_poses, base_expressions, free_filters` | 主键: [scene_templates] template_id: balcony_01, bedroom_01, garden_01 ...等 5 个, [base_poses] pose_id: sit_01, stand_01, [base_expressions] expression_id: blink_01, smile_01, [free_filters] filter_id: cool_01, natural_01, soft_01 ...等 5 个
- **system_numerical_docs.json** (5.5 KB) | 顶级 Key: `system_summary, field_dictionary, relations_and_enums, implementation_notes`
- **system_schema.json** (2.6 KB) | 模块: UI透明化, 付费埋点, 免费产出, 商城系统联动, 图鉴系统联动, 场景布置, 场景模板切换, 姿势系统, 拍照模式, 换装系统
