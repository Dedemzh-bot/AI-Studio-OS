# 项目记忆 Codex

> 仅扫描业务数据表，已过滤框架文件、外键字段。
> ID 已做范围压缩 / 去重截断，防止 Token 爆炸。
> 主键/外键已严格区分：只记录本模块主键 ID。

## 系统概览
- 已有系统模块: 公会资金转化模块, 水域管理模块, 钓鱼流程模块, 鱼获仓库模块, 鱼饵商店模块

## 已占用的主键 ID（范围压缩 / 去重截断）
- 共 3 组
  - `[bait_shop] bait_id: 1`
  - `[fish_conversion] fish_id: 101 ~ 303`
  - `[fishing_zones] zone_id: 1 ~ 3`

## 业务数据表清单
- **system_numerical_data.json** (2.7 KB) | 顶级 Key: `fishing_zones, bait_shop, fishing_process, fish_inventory, fish_conversion` | 主键: [fishing_zones] zone_id: 1 ~ 3, [bait_shop] bait_id: 1, [fish_conversion] fish_id: 101 ~ 303
- **system_numerical_docs.json** (2.8 KB) | 顶级 Key: `system_summary, field_dictionary, relations_and_enums, implementation_notes`
- **system_schema.json** (3.5 KB) | 模块: 公会资金转化模块, 水域管理模块, 钓鱼流程模块, 鱼获仓库模块, 鱼饵商店模块
- **ui_config.json** (0.9 KB) | 顶级 Key: `ux_layout, ui_tokens, assets_and_content, screen_position`
