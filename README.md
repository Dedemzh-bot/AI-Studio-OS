# AI Studio OS

## 简介
- 一句话：AI 驱动的游戏研发自动化工具
- 核心能力：概念简案 → 主策草案 → 系统详细案 → 数值推演 → 技术架构 → UX蓝图 → 审计纠错回环
- 双管线：单技能管线 + 玩法系统管线

## 安装部署
- 前置条件：Python 3.10+、Git
- git clone <repo>
- pip install -r requirements.txt
- 配置 .env（LLM_API_KEY + LLM_BASE_URL）
- python server.py 或 双击 start.bat

## 使用方式
- 浏览器打开 http://localhost:8080
- 输入游戏概念 → 启动研发
- 按审批节点确认（HITL 人机协同）
- 右侧文件面板随时打开产物

## 项目结构
- 顶层目录树简表（Agents/ / Skills/ / Guards/ / Knowledge/）
- 各目录一句话说明

## Agent 角色
- Visionary（主策）、System Planner（系统策划）、Numerical Planner（数值）
- Tech Architect（主程）、UX Agent（表现层）、Audit Agent（审查）
- Classifier（分类路由）

## 状态机流程
- 技能管线 vs 系统管线（流程图）

## 配置
- .env 字段说明
- 支持任意 OpenAI 兼容 API

## 注意事项
- 当前版本需手动 git clone + pip install，无打包版
- 配表模块标记「待测试」
