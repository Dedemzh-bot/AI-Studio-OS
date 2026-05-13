# 冰霜炸弹技能数据验收表

## 字段说明

| 字段名 | 类型 | 必填 | 取值范围 | 说明 |
|--------|------|------|----------|------|
| skillId | 字符串 | 是 | 仅允许字母、数字和下划线（如 "frost_bomb_01"） | 技能的唯一标识符，用于区分不同技能 |
| baseDamage | 整数 | 是 | 0 或正整数 | 技能的基础伤害值，不能为负数 |
| freezeDuration | 浮点数 | 是 | 0 或正数（单位：秒） | 冰冻效果的持续时间，例如 3.5 表示3.5秒 |
| triggerSource | 对象 | 是 | 必须包含 sourceType、sourceId、position | 触发来源的追踪信息，用于防漏洞 |

### triggerSource 对象字段

| 字段名 | 类型 | 必填 | 取值范围 | 说明 |
|--------|------|------|----------|------|
| sourceType | 字符串 | 是 | "player" / "enemy" / "environment" / "item" | 触发来源的类型，限制为四种 |
| sourceId | 字符串 | 是 | 仅允许字母、数字和下划线 | 具体触发实体的ID，如 "player_001" |
| position | 对象 | 是 | 包含 x, y, z 三个数值 | 触发时的世界坐标，用于边界检测 |

### position 对象字段

| 字段名 | 类型 | 必填 | 取值范围 | 说明 |
|--------|------|------|----------|------|
| x | 浮点数 | 是 | 任意实数 | 世界坐标X |
| y | 浮点数 | 是 | 任意实数 | 世界坐标Y |
| z | 浮点数 | 是 | 任意实数 | 世界坐标Z |

## 防漏洞措施

1. **触发来源追踪**：每个冰霜炸弹爆炸必须记录触发来源（sourceType + sourceId），系统可据此判断是否由地图边缘爆炸等异常情况产生，防止无限刷怪。
2. **位置校验**：记录爆炸时的三维坐标，服务器可校验该位置是否在地图合法范围内，若超出边界则拒绝生成后续效果。
3. **枚举限制**：sourceType 仅允许四种预设值，防止伪造来源类型。
4. **非负约束**：伤害和冰冻时间不允许负数，避免逻辑异常。
5. **唯一标识**：skillId 和 sourceId 使用正则限制，防止注入或非法字符。

## 验收检查清单

- [ ] 所有必填字段（skillId, baseDamage, freezeDuration, triggerSource）均已提供
- [ ] skillId 格式正确（字母数字下划线）
- [ ] baseDamage 为非负整数
- [ ] freezeDuration 为非负浮点数
- [ ] triggerSource 包含 sourceType、sourceId、position
- [ ] sourceType 为 "player"、"enemy"、"environment"、"item" 之一
- [ ] sourceId 格式正确
- [ ] position 包含 x、y、z 三个数值
- [ ] 无额外字段（additionalProperties 为 false）