# 项目记忆 Codex

> 仅扫描业务数据表，已过滤框架文件、外键字段。
> ID 已做范围压缩 / 去重截断，防止 Token 爆炸。
> 主键/外键已严格区分：只记录本模块主键 ID。

## 系统概览
- 已有系统模块: friend_system

## 已占用的主键 ID（范围压缩 / 去重截断）
- （未检测到）

## 业务数据表清单
- **.web_prompt.json** (0.1 KB) | 顶级 Key: `prompt, ts, answered`
- **project_meta.json** (0.1 KB) | 顶级 Key: `system_name, primary_tag, version`
- **system_numerical_data.json** (2.0 KB) | 顶级 Key: `continuous_formulas, discrete_milestones`
- **system_numerical_docs.json** (6.0 KB) | 顶级 Key: `system_summary, field_dictionary, relations_and_enums, implementation_notes`
- **system_schema.json** (0.9 KB) | 模块: friend_system
