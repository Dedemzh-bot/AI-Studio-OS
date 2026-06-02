# 背包系统 - 程序开发蓝图

## 一、 整体架构概述
背包系统是一个**纯客户端-服务端强同步**的仓储模块，核心性能瓶颈在于**高并发写操作的数据一致性**（多系统同时增删道具）以及**前端大量道具列表的流畅渲染**。系统采用**服务端权威校验 + 客户端虚拟列表渲染**的架构模式，所有道具的增删改查操作必须经过服务端校验并实时落盘，排序/筛选/搜索等纯展示操作仅在客户端本地执行。

## 二、 前端模块划分 (Client)

### 2.1 UI 组件层
- **背包主界面 (InventoryMainPanel)**：包含顶部栏（格位显示、扩容按钮、搜索框）、分类Tab栏、道具列表区、底部栏（排序/筛选/批量操作按钮）
- **道具卡片 (ItemCard)**：图标（`item_icon_size`=64px）、名称、数量、稀有度边框（N/R/SR/SSR）
- **详情弹窗 (ItemDetailPopup)**：道具信息展示、属性展示、来源信息、操作按钮（使用/分解/出售/合成）
- **二次确认弹窗 (ConfirmPopup)**：分解/出售/合成前的确认弹窗，显示产出预览
- **排序面板 (SortPanel)**：排序维度选择（稀有度/类型/获取时间/数量）与升序/降序切换
- **筛选面板 (FilterPanel)**：筛选条件选择（类型/稀有度/是否可堆叠）
- **搜索框 (SearchBar)**：支持模糊匹配，实时显示搜索结果
- **扩容提示弹窗 (ExpandPopup)**：扩容成功/失败提示
- **溢出提示弹窗 (OverflowPopup)**：背包已满时提示道具已发至邮件
- **空状态占位图 (EmptyState)**：筛选/搜索无结果时显示“暂无道具”或“未找到相关道具”

### 2.2 表现层控制器
- **道具操作反馈控制器 (ItemActionFeedbackController)**：
  - 使用成功：道具图标闪烁后消失/数量更新，飘字“使用成功”
  - 分解/出售成功：道具图标消失，飘字“分解成功”/“出售成功”，显示获得数量
  - 合成成功：播放合成动画（光效/粒子），飘字“合成成功”
  - 操作失败：弹窗显示具体失败原因
  - 条件不满足：按钮置灰并显示条件提示
  - 网络中断：操作回滚，弹窗提示“网络异常，请重试”
- **背包扩容反馈控制器 (ExpandFeedbackController)**：
  - 扩容成功：格位数更新，飘字“背包已扩容”
  - 已达上限：提示“背包已达上限”
- **溢出处理反馈控制器 (OverflowFeedbackController)**：
  - 获取道具时背包已满：弹窗提示“背包已满，道具已发送至邮件”
- **列表渲染控制器 (ListRenderController)**：
  - 采用虚拟列表技术，仅渲染可视区域内的道具卡片
  - 排序/筛选/搜索操作实时更新列表，不涉及后台请求

## 三、 后端逻辑划分 (Server)

### 3.1 持久化数据 (DB)
- **玩家背包表 (player_inventory)**：
  - `max_slots` (int, 默认值50)：背包最大格位数
  - `current_slots` (int, 默认值0)：当前已使用的背包格位数
  - `items` (json数组)：道具列表，每个元素包含 `item_id`, `quantity`, `stack_limit` 等字段
  - `materials` (json数组)：材料列表，结构与 `items` 类似
- **玩家货币表 (player_currency)**：
  - `currency_balance` (int, 默认值0)：基础货币数量
- **玩家邮件表 (player_mail)**：
  - `inbox` (json数组)：邮件列表，每个元素包含 `mail_id`, `title`, `content`, `attachments`, `expire_time` 等字段
- **活动道具表 (activity_items)**：
  - `activity_items` (json数组)：活动道具列表，每个元素包含 `item_id`, `quantity`

### 3.2 核心校验逻辑
- **使用道具校验**：
  - 校验道具是否存在且数量 > 0
  - 校验 `use_conditions` 中的前置条件（如角色是否拥有、是否已解锁、是否达到使用等级）
  - 校验通过后执行使用逻辑，减少道具数量，若归零则移除
- **分解/出售校验**：
  - 校验道具是否存在且数量 > 0
  - 校验通过后移除道具，按 `decompose_output`/`sale_output` 增加对应材料/货币
- **合成校验**：
  - 校验背包中所有 `required_materials` 数量是否充足
  - 校验背包容量是否足够容纳产出道具
  - 校验通过后消耗所有材料，产出目标道具
- **扩容校验**：
  - 校验扩容道具是否存在且数量 > 0
  - 校验 `max_slots` 是否已达 `max_slot_limit`（500）
  - 校验通过后增加 `max_slots`（+5），消耗扩容道具
- **溢出处理校验**：
  - 校验 `current_slots >= max_slots` 时，新道具不进入背包，生成溢出邮件
  - 邮件保留 `overflow_mail_retention_days`（30天），到期自动删除
- **活动道具回收校验**：
  - 活动结束后扫描所有玩家背包，查找活动道具ID列表
  - 按 `activity_item_conversion_rate`（10.0）转化为基础货币
  - 若玩家离线，在下次登录时执行回收
- **数据一致性校验**：
  - 所有写操作采用事务回滚机制，操作失败时回滚至操作前状态
  - 同一时间只允许一个写操作，通过写锁机制防止并发冲突
  - 写操作按时间顺序排队执行

## 四、 前后端通信协议 (API & 数据对接)

### 4.1 核心通信接口
- **`GetInventory`**: C->S / 请求参数: 无 / 返回参数: `{ max_slots, current_slots, items[], materials[] }`
- **`UseItem`**: C->S / 请求参数: `{ item_id, quantity }` / 返回参数: `{ success, error_code, updated_items[], updated_materials[] }`
- **`DecomposeItem`**: C->S / 请求参数: `{ item_id, quantity }` / 返回参数: `{ success, error_code, removed_item_id, added_materials[], added_currency }`
- **`SellItem`**: C->S / 请求参数: `{ item_id, quantity }` / 返回参数: `{ success, error_code, removed_item_id, added_currency }`
- **`SynthesizeItem`**: C->S / 请求参数: `{ recipe_id }` / 返回参数: `{ success, error_code, consumed_materials[], produced_item }`
- **`ExpandInventory`**: C->S / 请求参数: `{ expand_item_id }` / 返回参数: `{ success, error_code, new_max_slots }`
- **`GetMail`**: C->S / 请求参数: 无 / 返回参数: `{ inbox[] }`
- **`ClaimMailAttachment`**: C->S / 请求参数: `{ mail_id }` / 返回参数: `{ success, error_code, claimed_items[], claimed_currency }`
- **`RecycleActivityItems`**: S->C / 推送参数: `{ recycled_items[], converted_currency }` / 说明: 活动结束后服务端主动推送回收结果
- **`OverflowWarning`**: S->C / 推送参数: `{ warning_days_remaining }` / 说明: 溢出邮件到期前7天发送提醒

### 4.2 数据同步协议
- **写操作队列**: 所有写操作请求按时间顺序排队，服务端依次处理
- **事务回滚**: 操作失败时，服务端返回 `transaction_rollback=true`，客户端回滚至操作前状态
- **锁状态同步**: 服务端维护 `lock_status`，写操作进行中时锁定，完成后解锁

## 五、 数值与配置表挂载
程序启动时，读取数值策划提供的 `system_numerical_data.json` 表格，挂载以下配置：

### 5.1 背包容量配置
- `initial_slot_count` (int, 默认值50)：初始背包格位数
- `max_slot_limit` (int, 默认值500)：背包最大格位上限
- `expand_slot_increment` (int, 默认值5)：每次扩容增加的格位数
- `expand_item_id` (string, 默认值'expand_ticket')：扩容道具ID

### 5.2 溢出邮件配置
- `overflow_mail_retention_days` (int, 默认值30)：溢出邮件保留天数
- `overflow_mail_warning_days` (int, 默认值7)：到期前提醒天数

### 5.3 扩容相关配置
- `daily_free_expand_limit` (int, 默认值1)：每日基础货币购买扩容道具次数上限
- `expand_fragment_required` (int, 默认值10)：合成完整扩容道具所需碎片数量
- `expand_item_count_in_gift` (int, 默认值3)：扩容礼包中包含的扩容道具数量
- `expand_monthly_card_duration` (int, 默认值30)：扩容月卡有效天数

### 5.4 活动道具回收配置
- `activity_item_conversion_rate` (float, 默认值10.0)：活动道具回收转化比例
- `activity_end_warning_days` (int, 默认值3)：活动结束前提醒天数

### 5.5 道具基础配置
- `stack_limit` (int, 默认值999)：单个道具最大堆叠数量
- `item_icon_size` (int, 默认值64)：道具卡片图标尺寸（像素）

### 5.6 排序/筛选默认配置
- `sort_options` (json数组, 默认值`[{'field':'acquire_time','order':'desc'}]`)：默认排序选项
- `filter_options` (json数组, 默认值空数组)：默认筛选条件
- `search_keyword` (string, 默认值空字符串)：默认搜索关键字

## 六、 开发优先级与依赖链路 (执行排期) ★ 核心

### 阶段一 (P0 - 底层数据与协议)
- **数据库建表**：创建 `player_inventory`、`player_currency`、`player_mail`、`activity_items` 表
- **定义API协议**：完成所有核心通信接口的请求/返回参数定义
- **后端核心校验逻辑**：实现使用、分解、出售、合成、扩容、溢出处理、活动回收的校验逻辑
- **数据一致性机制**：实现写操作队列、事务回滚、写锁机制
- **数值配置挂载**：读取 `system_numerical_data.json` 并加载至内存

### 阶段二 (P1 - 前端核心表现)
- **UI框架搭建**：实现背包主界面、道具卡片、详情弹窗、二次确认弹窗等核心UI组件
- **接入后端API**：前端对接所有核心通信接口，实现道具增删改查的完整流程
- **核心玩法跑通**：实现使用、分解、出售、合成、扩容的完整操作链路
- **排序/筛选/搜索**：实现前端本地的排序、筛选、搜索功能
- **溢出处理流程**：实现背包已满时的邮件生成与领取流程

### 阶段三 (P2 - 表现层打磨)
- **特效接入**：合成动画（光效/粒子）、道具图标闪烁效果
- **边缘异常兜底**：网络中断时的操作回滚与提示、按钮置灰逻辑、空状态占位图
- **活动道具回收**：活动结束后的自动回收逻辑与通知推送
- **性能优化**：虚拟列表技术的实现与调优、大量道具下的流畅度测试
- **扩容相关功能**：扩容礼包、扩容月卡、碎片合成的完整实现
- **邮件提醒**：溢出邮件到期前7天的提醒推送、活动结束前3天的提醒推送