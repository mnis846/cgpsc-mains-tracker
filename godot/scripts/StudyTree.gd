extends Node2D
class_name StudyTree
## A single permanent study-milestone tree with growth, bloom, fruit, and wilt states.
## Drawn procedurally so the garden looks premium without external sprite packs.

enum State { EMPTY, SAPLING, YOUNG, BLOOMED, FRUITED, WILTED }

signal growth_finished
signal bloom_finished
signal fruit_finished

const STATE_NAMES := {
	State.EMPTY: "empty",
	State.SAPLING: "sapling",
	State.YOUNG: "young",
	State.BLOOMED: "bloomed",
	State.FRUITED: "fruited",
	State.WILTED: "wilted",
}

@export var tree_id: int = -1
@export var is_permanent: bool = true
@export var is_active_slot: bool = false

var milestone: Dictionary = {}
var current_state: State = State.EMPTY
var growth_scale: float = 0.0
var bloom_amount: float = 0.0
var fruit_amount: float = 0.0
var wilt_amount: float = 0.0
var sway_phase: float = 0.0
var hover: bool = false

var _target_scale: float = 1.0
var _base_scale: float = 1.0
var _trunk_color: Color = Color("5D4037")
var _leaf_color: Color = Color("2E7D32")
var _leaf_color_b: Color = Color("66BB6A")
var _flower_color: Color = Color("F8BBD0")
var _fruit_color: Color = Color("E53935")
var _fruit_shine: Color = Color("FFD54F")

@onready var petals: GPUParticles2D = $PetalParticles
@onready var sparkles: GPUParticles2D = $SparkleParticles
@onready var dust: GPUParticles2D = $DustParticles
@onready var anim: AnimationPlayer = $AnimationPlayer
@onready var tooltip: Label = $Tooltip
@onready var shadow: Polygon2D = $Shadow


func _ready() -> void:
	sway_phase = randf() * TAU
	_base_scale = scale.x
	if tooltip:
		tooltip.visible = false
	_configure_particles()
	_apply_visual_instant(State.EMPTY)
	queue_redraw()


func _process(delta: float) -> void:
	# Gentle idle sway via rotation (cheap + readable)
	var wilt_dampen := 1.0 - wilt_amount * 0.7
	var sway := sin(Time.get_ticks_msec() * 0.0015 + sway_phase) * 0.035 * growth_scale * wilt_dampen
	rotation = sway
	if wilt_amount > 0.01:
		rotation += wilt_amount * 0.12
	queue_redraw()


func configure_from_milestone(data: Dictionary, animate: bool = false) -> void:
	milestone = data.duplicate(true)
	tree_id = int(data.get("id", tree_id))
	is_permanent = true
	is_active_slot = false
	var next := _state_from_milestone(data)
	if animate and current_state != next:
		await transition_to(next, true)
	else:
		_apply_visual_instant(next)
	_update_tooltip()


func configure_active(progress_days: int, wilted: bool, animate: bool = false) -> void:
	"""In-progress tree for the current streak slot (not yet a permanent milestone)."""
	is_permanent = false
	is_active_slot = true
	milestone = {"id": -1, "progress_days": progress_days, "wilted": wilted}
	var next: State
	if wilted:
		next = State.WILTED
	elif progress_days <= 0:
		next = State.EMPTY
	elif progress_days < 2:
		next = State.SAPLING
	else:
		next = State.YOUNG
	if animate:
		await transition_to(next, true)
	else:
		_apply_visual_instant(next)
	_update_tooltip()


func transition_to(next: State, animated: bool = true) -> void:
	var prev := current_state
	current_state = next
	if not animated or prev == next:
		_apply_visual_instant(next)
		return

	match next:
		State.SAPLING, State.YOUNG:
			await _animate_grow(next)
			growth_finished.emit()
		State.BLOOMED:
			if prev in [State.EMPTY, State.SAPLING]:
				await _animate_grow(State.YOUNG)
			await _animate_bloom()
			bloom_finished.emit()
		State.FRUITED:
			if prev in [State.EMPTY, State.SAPLING]:
				await _animate_grow(State.YOUNG)
			if prev != State.BLOOMED and bloom_amount < 0.5:
				await _animate_bloom()
			await _animate_fruit()
			fruit_finished.emit()
		State.WILTED:
			await _animate_wilt()
		State.EMPTY:
			_apply_visual_instant(State.EMPTY)
		_:
			_apply_visual_instant(next)
	_update_tooltip()


func play_plant_celebration() -> void:
	if dust:
		dust.restart()
		dust.emitting = true
	var tw := create_tween()
	scale = Vector2.ZERO
	tw.tween_property(self, "scale", Vector2.ONE * _base_scale, 0.85).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	await tw.finished


func _state_from_milestone(data: Dictionary) -> State:
	if bool(data.get("has_fruits", false)):
		return State.FRUITED
	if bool(data.get("has_flowers", false)):
		return State.BLOOMED
	return State.YOUNG


func _apply_visual_instant(state: State) -> void:
	current_state = state
	match state:
		State.EMPTY:
			growth_scale = 0.0
			bloom_amount = 0.0
			fruit_amount = 0.0
			wilt_amount = 0.0
			visible = false
		State.SAPLING:
			visible = true
			growth_scale = 0.35
			bloom_amount = 0.0
			fruit_amount = 0.0
			wilt_amount = 0.0
			_set_healthy_palette()
		State.YOUNG:
			visible = true
			growth_scale = 0.75
			bloom_amount = 0.0
			fruit_amount = 0.0
			wilt_amount = 0.0
			_set_healthy_palette()
		State.BLOOMED:
			visible = true
			growth_scale = 1.0
			bloom_amount = 1.0
			fruit_amount = 0.0
			wilt_amount = 0.0
			_set_healthy_palette()
			_set_petals_emitting(true)
		State.FRUITED:
			visible = true
			growth_scale = 1.0
			bloom_amount = 0.85
			fruit_amount = 1.0
			wilt_amount = 0.0
			_set_healthy_palette()
			_set_petals_emitting(true)
			if sparkles:
				sparkles.emitting = true
		State.WILTED:
			visible = true
			growth_scale = maxf(growth_scale, 0.45)
			bloom_amount = 0.0
			fruit_amount = 0.0
			wilt_amount = 1.0
			_set_wilt_palette()
			_set_petals_emitting(false)
			if sparkles:
				sparkles.emitting = false
	_update_shadow()
	queue_redraw()


func _set_healthy_palette() -> void:
	_trunk_color = Color("5D4037")
	_leaf_color = Color("1B5E20")
	_leaf_color_b = Color("66BB6A")
	_flower_color = Color("F8BBD0")
	_fruit_color = Color("E53935")
	_fruit_shine = Color("FFD54F")


func _set_wilt_palette() -> void:
	_trunk_color = Color("6D5C3F")
	_leaf_color = Color("A89B3A")
	_leaf_color_b = Color("C4B24A")
	_flower_color = Color("D7C48A")
	_fruit_color = Color("BCA06A")
	_fruit_shine = Color("C9B27A")


func _animate_grow(target_state: State) -> void:
	visible = true
	_set_healthy_palette()
	wilt_amount = 0.0
	var target_g := 0.35 if target_state == State.SAPLING else (0.75 if target_state == State.YOUNG else 1.0)
	if growth_scale < 0.05:
		scale = Vector2(0.15, 0.05) * _base_scale
	var tw := create_tween().set_parallel(true)
	tw.tween_property(self, "growth_scale", target_g, 0.9).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(self, "scale", Vector2.ONE * _base_scale, 0.9).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	if dust:
		dust.restart()
		dust.emitting = true
	await tw.finished
	current_state = target_state
	_update_shadow()


func _animate_bloom() -> void:
	_set_healthy_palette()
	growth_scale = maxf(growth_scale, 0.9)
	var tw := create_tween()
	tw.tween_property(self, "bloom_amount", 1.0, 1.1).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	_set_petals_emitting(true)
	if petals:
		petals.amount = 48
		petals.restart()
	await tw.finished
	current_state = State.BLOOMED
	if petals:
		petals.amount = 18


func _animate_fruit() -> void:
	var tw := create_tween()
	tw.tween_property(self, "fruit_amount", 1.0, 0.8).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	if sparkles:
		sparkles.restart()
		sparkles.emitting = true
	await tw.finished
	current_state = State.FRUITED


func _animate_wilt() -> void:
	_set_petals_emitting(false)
	if sparkles:
		sparkles.emitting = false
	var tw := create_tween().set_parallel(true)
	tw.tween_property(self, "wilt_amount", 1.0, 1.2).set_trans(Tween.TRANS_SINE)
	tw.tween_property(self, "bloom_amount", 0.0, 0.9)
	tw.tween_property(self, "fruit_amount", 0.0, 0.7)
	await tw.finished
	_set_wilt_palette()
	current_state = State.WILTED
	queue_redraw()


func _set_petals_emitting(on: bool) -> void:
	if petals:
		var bloomed := current_state in [State.BLOOMED, State.FRUITED] or bloom_amount > 0.2
		petals.emitting = on and bloomed and wilt_amount < 0.5


func _update_shadow() -> void:
	if not shadow:
		return
	shadow.visible = growth_scale > 0.05
	var w := 28.0 * growth_scale
	shadow.polygon = PackedVector2Array([
		Vector2(-w, 4), Vector2(w, 4), Vector2(w * 0.7, 12), Vector2(-w * 0.7, 12)
	])
	shadow.color = Color(0.1, 0.15, 0.08, 0.28 * growth_scale)


func _update_tooltip() -> void:
	if not tooltip:
		return
	if is_active_slot:
		if wilt_amount > 0.5:
			tooltip.text = "Streak paused — water me with study hours"
		else:
			var days := int(milestone.get("progress_days", 0))
			tooltip.text = "Growing… day %d / 4" % max(days, 1)
	elif not milestone.is_empty():
		var date_s := str(milestone.get("achieved_date", ""))
		var score = milestone.get("test_score", null)
		var bits: PackedStringArray = ["Tree #%d" % tree_id]
		if date_s != "":
			bits.append(date_s)
		if bool(milestone.get("has_flowers", false)):
			bits.append("🌸 bloomed")
		if bool(milestone.get("has_fruits", false)):
			bits.append("🍎 fruited")
		if score != null:
			bits.append("%s%% test" % str(score))
		tooltip.text = " · ".join(bits)
	else:
		tooltip.text = ""


func _make_circle_texture(size: int = 16, color: Color = Color.WHITE) -> Texture2D:
	var img := Image.create(size, size, false, Image.FORMAT_RGBA8)
	var c := Vector2(size * 0.5, size * 0.5)
	var r := size * 0.5
	for y in size:
		for x in size:
			var d := Vector2(x, y).distance_to(c) / r
			var a := clampf(1.0 - d, 0.0, 1.0)
			a = smoothstep(0.0, 1.0, a)
			img.set_pixel(x, y, Color(color.r, color.g, color.b, a * color.a))
	return ImageTexture.create_from_image(img)


func _configure_particles() -> void:
	var soft := _make_circle_texture(16, Color(1, 1, 1, 1))
	if petals:
		petals.emitting = false
		petals.amount = 18
		petals.lifetime = 4.5
		petals.preprocess = 1.0
		petals.explosiveness = 0.05
		petals.randomness = 0.6
		petals.visibility_rect = Rect2(-120, -180, 240, 260)
		petals.local_coords = false
		petals.texture = soft
		var mat := ParticleProcessMaterial.new()
		mat.particle_flag_disable_z = true
		mat.direction = Vector3(0.15, 1, 0)
		mat.spread = 55.0
		mat.initial_velocity_min = 8.0
		mat.initial_velocity_max = 28.0
		mat.gravity = Vector3(4, 22, 0)
		mat.scale_min = 0.45
		mat.scale_max = 1.1
		mat.color = Color("F8BBD0")
		mat.hue_variation_min = -0.05
		mat.hue_variation_max = 0.08
		mat.angular_velocity_min = -40.0
		mat.angular_velocity_max = 40.0
		petals.process_material = mat
		petals.position = Vector2(0, -70)

	if sparkles:
		sparkles.emitting = false
		sparkles.amount = 12
		sparkles.lifetime = 1.4
		sparkles.explosiveness = 0.2
		sparkles.texture = soft
		var sm := ParticleProcessMaterial.new()
		sm.particle_flag_disable_z = true
		sm.direction = Vector3(0, -1, 0)
		sm.spread = 180.0
		sm.initial_velocity_min = 6.0
		sm.initial_velocity_max = 18.0
		sm.gravity = Vector3(0, -6, 0)
		sm.scale_min = 0.25
		sm.scale_max = 0.7
		sm.color = Color("FFE082")
		sparkles.process_material = sm
		sparkles.position = Vector2(0, -55)

	if dust:
		dust.emitting = false
		dust.one_shot = true
		dust.amount = 20
		dust.lifetime = 0.9
		dust.explosiveness = 0.85
		dust.texture = soft
		var dm := ParticleProcessMaterial.new()
		dm.particle_flag_disable_z = true
		dm.direction = Vector3(0, -1, 0)
		dm.spread = 80.0
		dm.initial_velocity_min = 20.0
		dm.initial_velocity_max = 60.0
		dm.gravity = Vector3(0, 40, 0)
		dm.scale_min = 0.25
		dm.scale_max = 0.75
		dm.color = Color("A5D6A7")
		dust.process_material = dm
		dust.position = Vector2(0, 0)


func _draw() -> void:
	if growth_scale <= 0.01:
		return

	var g := growth_scale
	var wilt := wilt_amount

	# Ground tuft
	draw_colored_polygon(
		PackedVector2Array([
			Vector2(-18 * g, 2), Vector2(18 * g, 2),
			Vector2(12 * g, 8), Vector2(-12 * g, 8)
		]),
		Color(0.25, 0.45, 0.22, 0.55 * (1.0 - wilt * 0.3))
	)

	# Trunk
	var trunk_h := 78.0 * g
	var trunk_w := 9.0 + 7.0 * g
	var lean := wilt * 10.0
	var trunk_col := _trunk_color.lerp(Color("8D6E3F"), wilt * 0.5)
	var trunk_pts := PackedVector2Array([
		Vector2(-trunk_w * 0.45 + lean * 0.2, 0),
		Vector2(trunk_w * 0.45 + lean * 0.2, 0),
		Vector2(trunk_w * 0.32 + lean, -trunk_h),
		Vector2(-trunk_w * 0.32 + lean, -trunk_h),
	])
	draw_colored_polygon(trunk_pts, trunk_col)
	# Bark highlight
	draw_line(Vector2(-trunk_w * 0.15 + lean * 0.5, -4), Vector2(-trunk_w * 0.1 + lean, -trunk_h + 6), trunk_col.lightened(0.18), 2.0)

	# Foliage layers (cherry-canopy style stacked ellipses approximated as polygons)
	var canopy_y := -trunk_h + 8.0
	var canopy_scale := 0.55 + 0.45 * clampf((g - 0.3) / 0.7, 0.0, 1.0)
	if current_state == State.SAPLING or g < 0.45:
		_draw_ellipse_poly(Vector2(lean * 0.6, canopy_y + 10), 16 * g, 12 * g, _leaf_color_b)
		_draw_ellipse_poly(Vector2(lean * 0.6, canopy_y + 4), 12 * g, 10 * g, _leaf_color)
	else:
		var leaf_a := _leaf_color.lerp(Color("A89B3A"), wilt)
		var leaf_b := _leaf_color_b.lerp(Color("C4B24A"), wilt)
		_draw_ellipse_poly(Vector2(-22 * canopy_scale + lean, canopy_y + 18), 30 * canopy_scale, 22 * canopy_scale, leaf_b)
		_draw_ellipse_poly(Vector2(24 * canopy_scale + lean, canopy_y + 16), 28 * canopy_scale, 20 * canopy_scale, leaf_b.darkened(0.05))
		_draw_ellipse_poly(Vector2(lean * 0.8, canopy_y + 4), 40 * canopy_scale, 28 * canopy_scale, leaf_a)
		_draw_ellipse_poly(Vector2(-12 * canopy_scale + lean, canopy_y - 10), 26 * canopy_scale, 18 * canopy_scale, leaf_b.lightened(0.08))
		_draw_ellipse_poly(Vector2(14 * canopy_scale + lean, canopy_y - 12), 24 * canopy_scale, 17 * canopy_scale, leaf_a.lightened(0.05))
		_draw_ellipse_poly(Vector2(lean, canopy_y - 22), 22 * canopy_scale, 16 * canopy_scale, leaf_b.lightened(0.12))

	# Cherry blossoms
	if bloom_amount > 0.05 and wilt < 0.6:
		_draw_flowers(canopy_y, canopy_scale, lean, bloom_amount)

	# Shiny fruits
	if fruit_amount > 0.05 and wilt < 0.5:
		_draw_fruits(canopy_y, canopy_scale, lean, fruit_amount)

	# Hover glow ring
	if hover:
		draw_arc(Vector2(0, 6), 26 * g, 0, TAU, 32, Color(1, 0.95, 0.6, 0.35), 2.0, true)


func _draw_ellipse_poly(center: Vector2, rx: float, ry: float, color: Color, segs: int = 18) -> void:
	var pts := PackedVector2Array()
	for i in segs:
		var a := TAU * float(i) / float(segs)
		pts.append(center + Vector2(cos(a) * rx, sin(a) * ry))
	draw_colored_polygon(pts, color)


func _draw_flowers(canopy_y: float, canopy_scale: float, lean: float, amount: float) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = int(tree_id * 9973 + 42) if tree_id >= 0 else 12345
	var count := int(14 * amount * canopy_scale)
	for i in count:
		var ox := (rng.randf() * 2.0 - 1.0) * 34.0 * canopy_scale + lean
		var oy := canopy_y - 8 + (rng.randf() * 2.0 - 1.0) * 28.0 * canopy_scale
		var r := 2.2 + rng.randf() * 2.4
		var c := _flower_color.lerp(Color("FFFFFF"), rng.randf() * 0.45)
		c.a = 0.75 + amount * 0.25
		# 5-petal simple blossom
		for p in 5:
			var ang := TAU * float(p) / 5.0 + rng.randf() * 0.2
			var petal_c := c.lightened(0.05 * (p % 2))
			_draw_ellipse_poly(Vector2(ox, oy) + Vector2(cos(ang), sin(ang)) * r * 0.7, r * 0.55, r * 0.35, petal_c, 8)
		draw_circle(Vector2(ox, oy), r * 0.35, Color("FFF59D").lerp(Color("F48FB1"), 0.3))


func _draw_fruits(canopy_y: float, canopy_scale: float, lean: float, amount: float) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = int(tree_id * 1337 + 7) if tree_id >= 0 else 99
	var count := int(6 * amount)
	for i in count:
		var ox := (rng.randf() * 2.0 - 1.0) * 28.0 * canopy_scale + lean
		var oy := canopy_y + 6 + (rng.randf() * 2.0 - 1.0) * 18.0 * canopy_scale
		var r := 3.5 + rng.randf() * 1.8
		var gold := rng.randf() > 0.55
		var body := _fruit_shine if gold else _fruit_color
		draw_circle(Vector2(ox, oy), r, body)
		draw_circle(Vector2(ox - r * 0.3, oy - r * 0.3), r * 0.28, Color(1, 1, 1, 0.55))
		draw_line(Vector2(ox, oy - r), Vector2(ox, oy - r - 3), Color("4E342E"), 1.2)
		# Soft glow
		draw_circle(Vector2(ox, oy), r * 1.6, Color(body.r, body.g, body.b, 0.12 * amount))


func _on_area_mouse_entered() -> void:
	hover = true
	if tooltip and tooltip.text != "":
		tooltip.visible = true
	var tw := create_tween()
	tw.tween_property(self, "scale", Vector2.ONE * _base_scale * 1.06, 0.15)


func _on_area_mouse_exited() -> void:
	hover = false
	if tooltip:
		tooltip.visible = false
	var tw := create_tween()
	tw.tween_property(self, "scale", Vector2.ONE * _base_scale, 0.15)
