# 背包系统 - UI 交互蓝图与生图清单

---

## 界面一：背包主界面

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 当前背包格位使用数 / 总格位数（如：50/200）
  - 当前分类Tab（全部、消耗品、装备、礼物、皮肤、活动道具、材料）
  - 当前排序状态（如：按获取时间降序）
  - 当前筛选条件数量（如：已选择2个筛选条件）
  - 搜索框中的关键字
  - 道具卡片列表：每个卡片包含道具图标、道具名称、当前持有数量、稀有度边框/角标
  - 底部栏的排序按钮、筛选按钮、批量操作按钮
- **【必须包含的操作】**：
  - 点击分类Tab切换道具类型
  - 点击排序按钮弹出排序选项列表，选择排序维度与升序/降序
  - 点击筛选按钮弹出筛选条件面板，选择/取消筛选条件
  - 点击搜索框输入关键字，实时匹配
  - 点击道具卡片弹出详情弹窗
  - 点击扩容按钮（位于顶部栏格位数旁）
  - 点击批量操作按钮（如批量分解）
  - 长按道具卡片可拖拽至分解/出售/合成槽位 `[UX 自动补全]`
- **【状态流转与兜底】**：
  - 正常状态：显示所有道具卡片列表（按当前分类、排序、筛选、搜索条件）
  - 空状态（无任何道具）：显示占位缺省图与“背包空空如也”文本 `[UX 自动补全]`
  - 空状态（筛选/搜索无结果）：显示占位缺省图与“未找到相关道具”文本
  - 加载状态：显示骨架屏（道具卡片占位框）或转圈动画 `[UX 自动补全]`
  - 网络异常：顶部显示“网络连接异常，数据可能未更新”提示条 `[UX 自动补全]`
  - 背包已满：顶部显示“背包已满，新道具将暂存至邮件”提示条 `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game UI
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast, semi-transparent frosted glass background
  - **Layout**: Top status bar (slot count + expand button + search bar), below that a horizontal scrollable category tab bar, main content area is a vertical scrollable grid (2 columns) of item cards, bottom fixed bar with sort/filter/batch action buttons
  - **Key Components**: “Slot Counter with Expand Icon”, “Search Input Field”, “Category Tabs (All/Consumables/Equipment/Gifts/Skins/Event/Materials)”, “Item Card (Icon + Name + Quantity + Rarity Border)”, “Sort Dropdown”, “Filter Panel (expandable)”, “Batch Action Button”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout, inventory screen, mobile game UI
- **布局意图解析 (中文)**：采用顶部固定栏展示核心状态（格位、搜索），分类Tab可横向滑动以容纳未来可能的更多类型，主区域使用2列网格布局以最大化道具可见性，底部固定操作栏便于单手操作排序/筛选/批量功能。

---

## 界面二：道具详情弹窗

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 道具图标（大尺寸）
  - 道具名称
  - 稀有度标签（N/R/SR/SSR）
  - 道具类型（如：消耗品、装备）
  - 道具描述文本
  - 当前持有数量
  - 堆叠上限
  - 若为装备：基础属性列表（如攻击、防御）
  - 若为消耗品：使用效果描述
  - 来源信息（如“关卡掉落：第3章”、“商城购买”）
  - 操作按钮区域
- **【必须包含的操作】**：
  - 点击“使用”按钮（仅当道具可使用时显示且可用）
  - 点击“分解”或“出售”按钮（仅当道具可分解/出售时显示且可用）
  - 点击“合成”按钮（仅当道具可合成时显示且可用）
  - 点击弹窗外部或关闭按钮关闭弹窗
- **【状态流转与兜底】**：
  - 正常状态：显示完整道具信息与可用操作按钮
  - 道具数量为0时：“使用”/“分解”/“出售”按钮置灰，并显示“道具不足”提示 `[UX 自动补全]`
  - 使用条件不满足时（如角色未拥有、皮肤已解锁）：“使用”按钮置灰，并显示具体条件提示文本 `[UX 自动补全]`
  - 背包已满时（若操作涉及新道具进入背包）：“使用”/“合成”按钮置灰，并显示“背包已满”提示 `[UX 自动补全]`
  - 加载中（如点击操作后等待服务器响应）：按钮显示加载动画，禁止重复点击 `[UX 自动补全]`
  - 操作成功：弹窗关闭，主界面道具列表更新，飘字提示“使用成功”/“分解成功”/“出售成功”/“合成成功” `[UX 自动补全]`
  - 操作失败：弹窗内显示具体失败原因文本（如“网络异常，请重试”） `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game Popup Modal
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast, semi-transparent overlay background
  - **Layout**: Centered modal card with rounded corners. Top area: large item icon with rarity border. Middle area: item name, rarity label, type label, description text, quantity/stack info. If equipment: attribute list in 2 columns. Bottom area: source info line, then 1-3 action buttons (Use/Decompose/Sell/Craft) in a horizontal row
  - **Key Components**: “Large Item Icon”, “Rarity Badge”, “Item Name & Type”, “Description Text”, “Quantity & Stack Limit”, “Attribute List (if equipment)”, “Source Info”, “Action Buttons (Use/Decompose/Sell/Craft)”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout, item detail modal, popup
- **布局意图解析 (中文)**：采用居中弹窗设计，不遮挡主界面过多内容。顶部展示大图标吸引视觉焦点，中部按信息重要性分层展示（名称→描述→属性→来源），底部固定操作按钮区域便于玩家快速决策。

---

## 界面三：二次确认弹窗（分解/出售/合成确认）

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 操作标题（如“确认分解”、“确认出售”、“确认合成”）
  - 操作描述文本（如“将消耗以下道具，并获得：”）
  - 消耗道具列表（图标+名称+数量）
  - 获得道具/货币列表（图标+名称+数量）
  - 确认按钮（如“分解”、“出售”、“合成”）
  - 取消按钮
- **【必须包含的操作】**：
  - 点击确认按钮执行操作
  - 点击取消按钮关闭弹窗
- **【状态流转与兜底】**：
  - 正常状态：显示完整的消耗与获得预览
  - 加载中（点击确认后等待服务器响应）：确认按钮显示加载动画，禁止重复点击 `[UX 自动补全]`
  - 操作成功：弹窗关闭，主界面道具列表更新，飘字提示操作成功 `[UX 自动补全]`
  - 操作失败：弹窗内显示具体失败原因文本（如“网络异常，请重试”），按钮恢复可点击状态 `[UX 自动补全]`
  - 网络中断：操作回滚，弹窗显示“网络异常，请重试”提示 `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game Confirmation Popup Modal
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast, semi-transparent overlay background
  - **Layout**: Centered modal card. Top: title text (e.g., “Confirm Decompose”). Middle: description text, then two sections side by side or stacked: “Consume” list (icons + names + quantities) and “Obtain” list (icons + names + quantities), separated by an arrow or divider. Bottom: two buttons side by side (Cancel / Confirm)
  - **Key Components**: “Title Text”, “Description Text”, “Consume Item List”, “Obtain Item/Currency List”, “Cancel Button”, “Confirm Button”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout, confirmation modal, popup
- **布局意图解析 (中文)**：采用居中弹窗，清晰展示“消耗”与“获得”的对比关系，帮助玩家做出知情决策。底部双按钮设计（取消/确认）符合用户预期，防止误操作。

---

## 界面四：排序/筛选面板（弹出式）

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 排序选项列表（按稀有度、类型、获取时间、数量等），当前选中项高亮
  - 升序/降序切换按钮
  - 筛选条件列表（类型、稀有度、是否可堆叠等），已选条件高亮
  - 重置按钮
  - 应用/确认按钮
- **【必须包含的操作】**：
  - 点击排序选项切换排序维度
  - 点击升序/降序切换按钮
  - 点击筛选条件选择/取消
  - 点击重置按钮清空所有筛选条件
  - 点击应用/确认按钮关闭面板并应用设置
  - 点击面板外部或关闭按钮关闭面板（不保存更改） `[UX 自动补全]`
- **【状态流转与兜底】**：
  - 正常状态：显示所有排序/筛选选项，当前设置高亮
  - 无可用排序/筛选选项时：显示“暂无可用选项”文本 `[UX 自动补全]`
  - 应用后：面板关闭，主界面道具列表更新，排序/筛选按钮显示当前状态

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game Bottom Sheet / Popup Panel
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast, semi-transparent background
  - **Layout**: Bottom sheet panel that slides up from bottom. Top: title “Sort & Filter”. Upper section: sort options as horizontal chips (Rarity/Type/Time/Quantity) + ascending/descending toggle. Lower section: filter options as checkable list or chips (Type: All/Consumables/Equipment/Gifts/Skins/Event/Materials; Rarity: N/R/SR/SSR; Stackable: Yes/No). Bottom: Reset button (left) + Apply button (right)
  - **Key Components**: “Sort Chips”, “Ascending/Descending Toggle”, “Filter Checkboxes/Chips”, “Reset Button”, “Apply Button”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout, sort filter panel, bottom sheet
- **布局意图解析 (中文)**：采用底部弹出面板，不遮挡主界面内容，便于单手操作。排序和筛选整合在同一面板中，减少玩家操作步骤。使用芯片式选择器节省空间，支持多选筛选条件。

---

## 界面五：扩容确认弹窗

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 当前格位数与扩容后格位数（如：50 → 70）
  - 消耗道具/货币信息（图标+名称+数量）
  - 确认扩容按钮
  - 取消按钮
- **【必须包含的操作】**：
  - 点击确认扩容按钮执行扩容
  - 点击取消按钮关闭弹窗
- **【状态流转与兜底】**：
  - 正常状态：显示扩容前后对比与消耗信息
  - 已达扩容上限时：确认按钮置灰，显示“背包已达上限”提示 `[UX 自动补全]`
  - 消耗道具不足时：确认按钮置灰，显示“道具不足”提示 `[UX 自动补全]`
  - 加载中（点击确认后等待服务器响应）：确认按钮显示加载动画，禁止重复点击 `[UX 自动补全]`
  - 扩容成功：弹窗关闭，主界面格位数更新，飘字提示“背包已扩容” `[UX 自动补全]`
  - 扩容失败：弹窗内显示具体失败原因文本 `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game Confirmation Popup Modal
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast, semi-transparent overlay background
  - **Layout**: Centered modal card. Top: title “Expand Backpack”. Middle: visual comparison of slots before/after (e.g., “50 → 70”), consumption info (icon + name + quantity). Bottom: two buttons side by side (Cancel / Expand)
  - **Key Components**: “Title Text”, “Slot Count Comparison (Before → After)”, “Consumption Item/Currency Display”, “Cancel Button”, “Expand Button”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout, expansion confirmation modal
- **布局意图解析 (中文)**：采用居中弹窗，通过“扩容前→扩容后”的数值对比直观展示扩容收益，帮助玩家决策。消耗信息清晰展示，避免玩家误操作。

---

## 界面六：批量操作界面（如批量分解）

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 可批量操作的道具列表（每个道具显示图标、名称、数量、可操作数量选择器）
  - 已选道具总数与预计获得材料/货币预览
  - 执行批量操作按钮
  - 取消/退出按钮
- **【必须包含的操作】**：
  - 点击道具卡片选择/取消选择
  - 通过数量选择器调整每个道具的操作数量（如分解数量）
  - 点击执行批量操作按钮
  - 点击取消/退出按钮返回主界面
- **【状态流转与兜底】**：
  - 正常状态：显示所有可批量操作的道具列表，默认未选择
  - 未选择任何道具时：执行按钮置灰，显示“请选择道具”提示 `[UX 自动补全]`
  - 选择道具后：执行按钮亮起，预览区域更新预计获得材料/货币
  - 加载中（点击执行后等待服务器响应）：执行按钮显示加载动画，禁止重复点击 `[UX 自动补全]`
  - 操作成功：界面关闭，主界面道具列表更新，飘字提示批量操作成功 `[UX 自动补全]`
  - 操作失败：界面内显示具体失败原因文本 `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game Batch Operation Screen
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast
  - **Layout**: Top bar with title “Batch Decompose” and close button. Main content: vertical scrollable list of item cards, each card has icon, name, quantity, and a +/- stepper for selecting how many to decompose. Bottom fixed bar: preview of total items selected and estimated materials/currency to obtain, plus “Execute” button
  - **Key Components**: “Item Card with Quantity Stepper”, “Selected Items Preview”, “Estimated Rewards Preview”, “Execute Button”, “Close Button”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout, batch operation screen, inventory management
- **布局意图解析 (中文)**：采用全屏界面以容纳更多道具，每个道具卡片内置数量选择器（+/- 步进器）便于精确控制操作数量。底部固定预览栏实时反馈总收益，帮助玩家决策。