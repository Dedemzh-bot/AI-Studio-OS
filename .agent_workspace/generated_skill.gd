extends Node
class_name SkillEMPBlast

const SKILL_ID := "sk_elec_emp_blast"
const SKILL_NAME := "电磁脉冲"
const SKILL_DESCRIPTION := "释放一道电磁脉冲波，对范围内机械单位造成伤害并短暂瘫痪"
const BASE_DAMAGE := 70
const PARALYZE_DURATION := 2.0
const EFFECT_RADIUS := 80
const TRIGGER_SOURCE_ID := "Engineer_009"
const TARGET_FILTER := {"unit_type": "mechanical"}
const DAMAGE_SOURCE_TAG := "skill_emp_blast"

var trigger_source: Node

func _init(source: Node) -> void:
	trigger_source = source

func execute() -> void:
	var targets := _get_targets_in_radius()
	for target in targets:
		if _is_mechanical(target):
			_apply_damage(target)
			_apply_paralyze(target)

func _get_targets_in_radius() -> Array:
	var space_state := trigger_source.get_world_3d().direct_space_state
	var query := PhysicsShapeQueryParameters3D.new()
	var sphere := SphereShape3D.new()
	sphere.radius = EFFECT_RADIUS
	query.shape = sphere
	query.transform = Transform3D.IDENTITY.translated(trigger_source.global_position)
	query.collision_mask = 1
	return space_state.intersect_shape(query)

func _is_mechanical(target: Node) -> bool:
	return target.has_meta("unit_type") and target.get_meta("unit_type") == "mechanical"

func _apply_damage(target: Node) -> void:
	if target.has_method("take_damage"):
		target.take_damage(BASE_DAMAGE, DAMAGE_SOURCE_TAG)

func _apply_paralyze(target: Node) -> void:
	if target.has_method("apply_status"):
		target.apply_status("paralyze", PARALYZE_DURATION)