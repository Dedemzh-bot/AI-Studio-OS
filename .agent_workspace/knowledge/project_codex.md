# 项目记忆 Codex

> 仅扫描业务数据表，已过滤框架文件、外键字段。
> ID 已做范围压缩 / 去重截断，防止 Token 爆炸。
> 主键/外键已严格区分：只记录本模块主键 ID。

## 系统概览
- 已有系统模块: 新增全局数据表, 旧系统与数据联动, 核心规则与玩法机制, 经济循环与商业化埋点, 表现层与角色展示联动, 角色私人宿舍

## 已占用的主键 ID（范围压缩 / 去重截断）
- （未检测到）

## 业务数据表清单
- **system_numerical_data.json** (4.0 KB) | 顶级 Key: `dorm_furniture, dorm_pose, dorm_costume, dorm_minigame, device_quality_preset`
- **system_numerical_docs.json** (4.3 KB) | 顶级 Key: `system_summary, field_dictionary, relations_and_enums, implementation_notes`
- **system_schema.json** (0.8 KB) | 模块: 新增全局数据表, 旧系统与数据联动, 核心规则与玩法机制, 经济循环与商业化埋点, 表现层与角色展示联动, 角色私人宿舍
