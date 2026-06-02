# 项目记忆 Codex

> 仅扫描业务数据表，已过滤框架文件、外键字段。
> ID 已做范围压缩 / 去重截断，防止 Token 爆炸。
> 主键/外键已严格区分：只记录本模块主键 ID。

## 系统概览
- 已有系统模块: activity_system, data_sync, economy_system, inventory_system, item_management, mail_system, player_inventory, ui_display

## 已占用的主键 ID（范围压缩 / 去重截断）
- 共 2 组
  - `[inventory_system] expand_item_id: expand_ticket`
  - `[player_inventory] expand_item_id: expand_ticket`

## 业务数据表清单
- **.web_prompt.json** (0.1 KB) | 顶级 Key: `prompt, ts, answered`
- **project_meta.json** (0.1 KB) | 顶级 Key: `system_name, primary_tag, version`
- **system_numerical_data.json** (4.5 KB) | 顶级 Key: `inventory_system, item_management, player_inventory, mail_system, economy_system, activity_system, ui_display, data_sync` | 主键: [inventory_system] expand_item_id: expand_ticket, [player_inventory] expand_item_id: expand_ticket
- **system_numerical_docs.json** (7.5 KB) | 顶级 Key: `system_summary, field_dictionary, relations_and_enums, implementation_notes`
- **system_schema.json** (2.5 KB) | 模块: activity_system, data_sync, economy_system, inventory_system, item_management, mail_system, player_inventory, ui_display
