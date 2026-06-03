# 角色宿舍 - UI 交互蓝图与生图清单

---

## 界面一：宿舍主入口（主界面按钮）

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 主界面“宿舍”入口按钮（常驻显示）
  - 按钮状态：可用/置灰（若玩家未拥有任何角色）
- **【必须包含的操作】**：
  - 点击入口按钮 → 进入角色选择界面
- **【状态流转与兜底】**：
  - 正常状态：按钮可点击，进入角色选择
  - 空状态（无角色）：按钮置灰，点击后弹出提示“请先获取一名角色” `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game UI
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast
  - **Layout**: Bottom navigation bar with icon + label for "Dormitory" entry
  - **Key Components**: “Dormitory” icon button, optional badge for new content
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout.
- **布局意图解析 (中文)**：采用底部导航栏常驻入口，符合手游操作习惯，便于玩家快速访问，同时按钮图标可承载角色头像预览等未来扩展。

---

## 界面二：角色选择界面

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 玩家所有已获取角色的头像、名称
  - 当前选中角色的高亮状态
- **【必须包含的操作】**：
  - 横向滑动列表浏览角色
  - 点击角色头像 → 选中并加载该角色宿舍
- **【状态流转与兜底】**：
  - 正常状态：横向滑动列表展示所有角色
  - 加载状态：显示加载动画与进度条 `[UX 自动补全]`
  - 空状态（无角色）：显示缺省图与“暂无角色”提示 `[UX 自动补全]`
  - 加载失败：显示“加载失败，请重试”提示与重试按钮 `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game UI / Popup Modal
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast
  - **Layout**: Full-screen modal with horizontal scrollable avatar list at center, selected avatar highlighted with glow border
  - **Key Components**: “Avatar Cards” (circular portrait + name label), “Loading Bar”, “Empty State Placeholder”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout.
- **布局意图解析 (中文)**：全屏弹窗展示角色列表，横向滑动可容纳较多角色，选中高亮便于玩家确认当前选择，加载进度条提供明确等待反馈。

---

## 界面三：宿舍场景主界面（核心交互界面）

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 角色模型（当前姿势、表情、装扮）
  - 场景模板（背景环境）
  - 已放置的家具/装饰品
  - 功能按钮组：换装、姿势、表情、场景布置、场景模板切换、拍照、方案保存/切换、隐藏UI、重置视角
  - 当前方案名称（若有）
- **【必须包含的操作】**：
  - 点击换装按钮 → 进入换装界面
  - 点击姿势按钮 → 弹出姿势选择面板
  - 点击表情按钮 → 弹出表情选择面板
  - 点击场景布置按钮 → 进入布置模式
  - 点击场景模板切换按钮 → 弹出模板选择面板
  - 点击拍照按钮 → 进入拍照模式
  - 点击方案保存按钮 → 弹出命名输入框
  - 点击方案切换按钮 → 弹出方案列表
  - 点击隐藏UI按钮 → 一键隐藏所有UI
  - 点击重置视角按钮 → 镜头恢复默认视角
  - 自由拖动视角浏览场景
- **【状态流转与兜底】**：
  - 正常状态：角色与场景完整展示，功能按钮以半透明毛玻璃样式悬浮
  - 隐藏UI状态：所有UI消失，仅保留角色与场景
  - 加载状态（首次进入）：场景淡入动画 `[UX 自动补全]`
  - 数据损坏状态：自动重置为默认配置 `[UX 自动补全]`
  - 网络异常：不影响本地操作，分享功能不可用时提示 `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game UI / 3D Scene Overlay
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast, frosted glass UI
  - **Layout**: Full 3D scene background, character centered, semi-transparent floating action buttons arranged in a vertical column on the right side (换装, 姿势, 表情, 布置, 模板, 拍照, 方案, 隐藏UI, 重置视角), top-left for scheme name
  - **Key Components**: “Floating Action Buttons” (icon only), “Character Model”, “Scene Environment”, “Furniture Objects”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout.
- **布局意图解析 (中文)**：采用全屏3D场景作为背景，角色居中展示最大化视觉冲击，功能按钮以半透明毛玻璃悬浮于右侧，不遮挡角色主体，符合项目宪法“严禁大面积遮挡角色模型”的红线。

---

## 界面四：换装界面

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 角色模型（实时预览换装效果）
  - 所有已拥有的皮肤/配件列表，按部位分类（服装、头饰、武器外观等）
  - 已装备项的“已装备”标签
  - 确认/取消按钮
- **【必须包含的操作】**：
  - 点击任意皮肤/配件 → 角色模型实时预览切换
  - 点击“确认”按钮 → 保存装扮状态，关闭界面
  - 点击“取消”按钮 → 恢复至进入前状态，关闭界面
- **【状态流转与兜底】**：
  - 正常状态：网格列表展示可用皮肤/配件，角色实时预览
  - 空状态（无可用装扮）：换装按钮置灰，提示“暂无可用装扮” `[UX 自动补全]`
  - 预览退出：若玩家在预览状态下退出，自动恢复至进入前状态 `[UX 自动补全]`
  - 多部位切换：所有切换操作在确认后统一保存 `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game UI / Popup Modal
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast
  - **Layout**: Left side: full-height character preview with rotation animation; Right side: vertical tabbed grid (by body part) of skin/accessory cards, each card showing thumbnail + name + “Equipped” badge; Bottom: “Confirm” and “Cancel” buttons
  - **Key Components**: “Character Preview”, “Category Tabs”, “Item Cards”, “Equipped Badge”, “Confirm/Cancel Buttons”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout.
- **布局意图解析 (中文)**：左侧角色预览区占据较大面积，便于玩家观察换装细节；右侧按部位分类的网格列表便于快速筛选；底部确认/取消按钮符合操作预期。

---

## 界面五：姿势选择面板

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 所有已解锁的姿势图标列表（站立、坐姿、依靠、蹲姿等）
  - 当前姿势高亮显示
  - 未解锁姿势显示锁图标与解锁条件
- **【必须包含的操作】**：
  - 点击任意姿势 → 角色模型实时切换至该姿势
  - 点击确认或关闭面板 → 姿势状态保存
- **【状态流转与兜底】**：
  - 正常状态：图标列表展示，当前姿势高亮
  - 空状态（仅基础姿势）：仅显示基础姿势 `[UX 自动补全]`
  - 场景切换适配：若切换场景模板后姿势无法适配，恢复为默认站立姿势 `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game UI / Bottom Sheet Panel
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast
  - **Layout**: Bottom sheet panel with horizontal scrollable icon list, each icon shows pose thumbnail, current pose highlighted with border, locked poses show lock icon + unlock condition text
  - **Key Components**: “Pose Icons”, “Highlight Border”, “Lock Icon”, “Unlock Condition Text”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout.
- **布局意图解析 (中文)**：底部面板弹出不遮挡角色主体，横向滑动列表可容纳较多姿势，高亮与锁图标提供清晰的状态反馈。

---

## 界面六：表情选择面板

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 所有已解锁的表情图标列表（微笑、眨眼、害羞、严肃等）
  - 当前表情高亮显示
  - 未解锁表情显示锁图标与解锁条件
- **【必须包含的操作】**：
  - 点击任意表情 → 角色面部实时切换至该表情
  - 点击确认或关闭面板 → 表情状态保存
- **【状态流转与兜底】**：
  - 正常状态：图标列表展示，当前表情高亮
  - 空状态（仅基础表情）：仅显示基础表情 `[UX 自动补全]`
  - 拍照模式兼容：表情切换不影响拍照模式状态 `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game UI / Bottom Sheet Panel
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast
  - **Layout**: Bottom sheet panel with horizontal scrollable icon list, each icon shows expression thumbnail (close-up of face), current expression highlighted with border, locked expressions show lock icon + unlock condition text
  - **Key Components**: “Expression Icons”, “Highlight Border”, “Lock Icon”, “Unlock Condition Text”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout.
- **布局意图解析 (中文)**：与姿势面板类似，采用底部面板+横向滑动列表，表情图标采用面部特写便于玩家识别，保持交互一致性。

---

## 界面七：场景布置模式

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 场景中所有已放置的家具/装饰品（显示半透明选中框）
  - 底部家具/装饰品分类列表（椅子、桌子、花束、灯光、背景板等）
  - 当前选中物件的操作手柄（位置微调、旋转、缩放）
  - 放置预览（绿色=可放置，红色=不可放置）
  - 保存/退出按钮
- **【必须包含的操作】**：
  - 从底部列表选择家具 → 物件跟随手指/鼠标移动
  - 点击场景中目标位置 → 放置物件
  - 选中已放置物件 → 进行位置微调、旋转、缩放
  - 点击“保存”按钮 → 保存当前布置状态
  - 点击“退出”按钮 → 退出布置模式
- **【状态流转与兜底】**：
  - 正常状态：布置模式开启，物件可交互
  - 碰撞检测：若与场景中其他物件或角色重叠，显示红色提示并禁止放置 `[UX 自动补全]`
  - 数量上限：达到 `[MAX_FURNITURE_COUNT]` 后禁止继续放置，提示“已达上限” `[UX 自动补全]`
  - 切换场景模板：弹出确认弹窗“切换场景将丢失未保存的布置，是否继续？” `[UX 自动补全]`
  - 断线：所有未保存的布置操作丢失 `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game UI / 3D Scene Editor Mode
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast
  - **Layout**: Full 3D scene with furniture objects showing semi-transparent selection boxes; Bottom: horizontal scrollable category tabs + item grid; Selected object shows manipulation handles (move, rotate, scale); Top: “Save” and “Exit” buttons; Placement preview shows green/red indicator
  - **Key Components**: “Furniture Objects”, “Selection Boxes”, “Category Tabs”, “Item Grid”, “Manipulation Handles”, “Placement Preview Indicator”, “Save/Exit Buttons”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout.
- **布局意图解析 (中文)**：布置模式下场景全屏展示，底部操作栏不遮挡主要画面，选中框与放置预览提供清晰的操作反馈，保存/退出按钮常驻顶部便于随时操作。

---

## 界面八：场景模板切换面板

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 所有已解锁的场景模板缩略图列表（卧室、阳台、花园、泳池边等）
  - 当前模板高亮显示
  - 未解锁模板显示锁图标与解锁条件
- **【必须包含的操作】**：
  - 点击任意模板 → 场景实时切换至该模板
  - 点击确认 → 切换生效
- **【状态流转与兜底】**：
  - 正常状态：缩略图列表展示，当前模板高亮
  - 空状态（仅一个模板）：切换按钮置灰 `[UX 自动补全]`
  - 切换时未保存布置：系统自动保存当前布置后再切换 `[UX 自动补全]`
  - 家具适配：无法适配的家具显示“已回收至背包”提示 `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game UI / Popup Modal
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast
  - **Layout**: Full-screen modal with grid layout of scene template thumbnails, current template highlighted with border, locked templates show lock icon + unlock condition text, “Confirm” button at bottom
  - **Key Components**: “Template Thumbnails”, “Highlight Border”, “Lock Icon”, “Unlock Condition Text”, “Confirm Button”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout.
- **布局意图解析 (中文)**：全屏网格展示模板缩略图，便于玩家预览场景效果，高亮与锁图标提供清晰的状态反馈，底部确认按钮统一操作。

---

## 界面九：拍照模式

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 全屏角色与场景（所有UI自动隐藏）
  - 镜头控制：双指缩放/旋转，单指平移
  - 滤镜选择面板（半透明毛玻璃样式）
  - 特效选择面板（半透明毛玻璃样式）
  - 角色调整按钮（微调位置、朝向、姿势、表情）
  - 快门按钮
  - 退出按钮
- **【必须包含的操作】**：
  - 自由旋转/缩放/平移镜头
  - 点击滤镜按钮 → 弹出滤镜选择面板，选择后画面实时叠加
  - 点击特效按钮 → 弹出特效选择面板，选择后画面实时叠加
  - 点击角色调整按钮 → 微调角色位置、朝向、姿势、表情
  - 点击快门按钮 → 截取当前画面
  - 截图后弹出分享面板（保存至本地相册/分享至社交平台）
  - 点击退出按钮 → 退出拍照模式，恢复UI显示
- **【状态流转与兜底】**：
  - 正常状态：全屏画面，无UI遮挡
  - 滤镜/特效选择：半透明面板不遮挡画面主体 `[UX 自动补全]`
  - 快门反馈：播放快门音效与闪光动画 `[UX 自动补全]`
  - 截图成功：显示“已保存至相册”提示 `[UX 自动补全]`
  - 存储空间不足：提示“存储空间不足，请清理后重试” `[UX 自动补全]`
  - 分享功能：若目标社交平台未安装，提示“请先安装该应用” `[UX 自动补全]`
  - 断线：拍照模式正常使用，但分享功能不可用 `[UX 自动补全]`
  - 切换角色：自动退出拍照模式并返回角色选择界面 `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game UI / Camera Mode Overlay
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast, frosted glass UI
  - **Layout**: Full-screen 3D scene with character, all UI hidden by default; Bottom: semi-transparent floating action bar with “Filter”, “Effect”, “Character Adjust”, “Shutter”, “Exit” buttons; Filter/Effect panels appear as semi-transparent overlay at bottom
  - **Key Components**: “Floating Action Bar”, “Filter/Effect Panels”, “Shutter Button”, “Character Adjust Controls”, “Share Panel”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout.
- **布局意图解析 (中文)**：拍照模式下UI全隐藏最大化画面展示，底部半透明操作栏不遮挡主体，滤镜/特效面板采用半透明毛玻璃样式保持画面可见，快门按钮突出设计便于快速操作。

---

## 界面十：方案保存与切换界面

### 1. 核心交互需求表 (Functional Checklist)
- **【前台可见数据】**：
  - 方案命名输入框（最多 `[SCHEME_NAME_MAX_LENGTH]` 个字符）
  - 已保存的方案列表（缩略图 + 名称）
  - 当前方案高亮显示
  - 方案槽位数量提示（已用/总数）
- **【必须包含的操作】**：
  - 输入方案名称 → 点击确认 → 保存当前状态为新方案
  - 点击已保存方案 → 场景与角色切换至该方案状态
  - 删除已保存方案（释放槽位）
- **【状态流转与兜底】**：
  - 正常状态：方案列表展示，可保存/切换/删除
  - 槽位已满：保存按钮置灰，提示“方案槽位已满，请先删除或付费解锁” `[UX 自动补全]`
  - 切换未保存：系统自动保存当前状态为临时方案（不占用槽位） `[UX 自动补全]`
  - 保存成功：显示“方案已保存”提示 `[UX 自动补全]`

### 2. 结构化生图 Prompt (Layout Inspiration)
- **Prompt (English)**:
  - **Type**: Mobile Game UI / Popup Modal
  - **Style**: Sci-fi, clean flat design, dark mode, high contrast
  - **Layout**: Full-screen modal with top section for “Save New Scheme” (name input + confirm button), bottom section for “Saved Schemes” (grid of thumbnails with name labels, current scheme highlighted, delete button on each card), slot count indicator at top
  - **Key Components**: “Name Input Field”, “Confirm Button”, “Scheme Thumbnails”, “Highlight Border”, “Delete Button”, “Slot Count Indicator”
  - **Keywords**: UI/UX, user interface architecture, wireframe layout, clean hierarchy, figma layout.
- **布局意图解析 (中文)**：全屏弹窗分为保存与切换两个区域，上方输入框便于快速保存新方案，下方网格展示已保存方案便于切换，槽位提示让玩家了解剩余空间，删除按钮提供管理功能。