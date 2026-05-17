# 项目记忆 Codex

> 自动生成于 `build_memory_codex.py`，为所有 Agent 提供全局上下文。
> 仅扫描业务数据表，已过滤框架运行文件 & 外键字段。
> ID 已做范围压缩（min~max）/ 截断去重，防止 Token 爆炸。

## 系统概览
- 已有系统模块: 公会商城刷新配置, 公会商城商品配置, 公会等级解锁槽位配置

## 已占用的业务 ID（范围压缩 / 去重截断）
- 共 1 组标识符
  - `[guild_shop_items] item_id: 1001 ~ 2001`

## 业务数据表清单
- **system_numerical_data.json** (1.5 KB) | 顶级 Key: `guild_shop_items, guild_shop_refresh, guild_level_slots` | ID: [guild_shop_items] item_id: 1001 ~ 2001
- **system_numerical_docs.json** (2.2 KB) | 顶级 Key: `system_summary, field_dictionary, relations_and_enums, implementation_notes`
- **system_schema.json** (0.6 KB) | 模块: 公会商城刷新配置, 公会商城商品配置, 公会等级解锁槽位配置
- **ui_config.json** (0.9 KB) | 顶级 Key: `ux_layout, ui_tokens, assets_and_content, screen_position`
