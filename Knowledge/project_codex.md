# 项目记忆 Codex

> 仅扫描业务数据表，已过滤框架文件、外键字段。
> ID 已做范围压缩 / 去重截断，防止 Token 爆炸。
> 主键/外键已严格区分：只记录本模块主键 ID。

## 系统概览
- 已有系统模块: activity_hall, daily_signin, inventory_system, mail_system

## 已占用的主键 ID（范围压缩 / 去重截断）
- 共 1 组
  - `[activity_config] activity_id: daily_signin, limited_instance`

## 业务数据表清单
- **.web_prompt.json** (0.1 KB) | 顶级 Key: `prompt, ts, answered`
- **project_meta.json** (0.1 KB) | 顶级 Key: `system_name, primary_tag, version`
- **system_numerical_data.json** (1.7 KB) | 顶级 Key: `activity_config, global_params` | 主键: [activity_config] activity_id: daily_signin, limited_instance
- **system_numerical_docs.json** (8.9 KB) | 顶级 Key: `system_summary, field_dictionary, relations_and_enums, implementation_notes`
- **system_schema.json** (1.8 KB) | 模块: activity_hall, daily_signin, inventory_system, mail_system
