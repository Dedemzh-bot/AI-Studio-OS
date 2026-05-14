extends Node
class_name IceFrostNova

var skill_id: String = "sk_ice_frost_nova"
var skill_name: String = "冰霜新星"
var description: String = "以自身为中心释放冰霜冲击波，冻结周围敌人"
var base_damage: int = 45
var freeze_duration: float = 2.5
var radius: float = 200.0
var trigger_source: Dictionary = {
	"source_type": "character",
	"source_id": "Mage_012"
}
var causality_trace: Array = [
	{
		"event": "skill_activated",
		"timestamp": 0,
		"source": "Mage_012"
	},
	{
		"event": "damage_dealt",
		"timestamp": 100,
		"source": "Mage_012"
	},
	{
		"event": "freeze_applied",
		"timestamp": 100,
		"source": "Mage_012"
	}
]

func _init() -> void:
	pass