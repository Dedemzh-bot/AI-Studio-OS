extends Node

var skill_id: String = "sk_shadow_step"
var skill_name: String = "暗影步"
var skill_description: String = "瞬间位移至目标身后，造成基础伤害并附加短暂减速效果。"
var base_damage: int = 35
var displacement_distance: float = 8.0
var trigger_source_id: String = "player_001"
var causal_chain_tag: String = "combat_evt_20250321_001"
var is_passive: bool = false
var cooldown_time: float = 12.0