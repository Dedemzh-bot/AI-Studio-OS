# 统一花名册 - 下游子 Agent 职能边界

## System Planner (系统策划)
- 职责：系统玩法架构设计，产出 MD 草案
- 擅长：游戏系统闭环、模块划分、成长维度定义
- 边界：不输出 JSON Schema，不负责数值填表

## Numerical Planner (数值策划)
- 职责：根据 Schema 生成具体数值成长表
- 擅长：Excel 级曲线推演、经济模型、数值平衡

## Schema Translator (格式翻译)
- 职责：将 MD 草案翻译为结构化 JSON Schema
- 擅长：精准格式转换

## Code Agent (程序执行)
- 职责：将校验通过的 JSON 翻译为 GDScript 代码

## UI Agent (UX/UI 设计)
- 职责：设计技能前端表现配置
- 边界：不涉及引擎动效

## Audit Agent (审查官)
- 职责：数值平衡性审查

## Combat Agent (战斗策划)
- 职责：根据概念简案生成战斗数值 JSON
