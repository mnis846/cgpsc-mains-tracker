extends Node2D
## Main garden view: sky, terrain, trees, ambient particles, HUD.

const StudyTreeScene := preload("res://scenes/StudyTree.tscn")

## Spiral / orchard layout slots (local coords on Ground layer).
const SLOT_RADIUS := 210.0
const SLOT_CENTER := Vector2(0, 40)

@onready var sky: ColorRect = $CanvasLayer/Sky
@onready var ground: Node2D = $World/Ground
@onready var trees_root: Node2D = $World/Trees
@onready var active_root: Node2D = $World/ActiveTree
@onready var fireflies: GPUParticles2D = $World/Fireflies
@onready var pollen: GPUParticles2D = $World/Pollen
@onready var warm_light: PointLight2D = $World/WarmLight
@onready var camera: Camera2D = $Camera2D
@onready var hud: CanvasLayer = $HUD
@onready var status_label: Label = $HUD/Margin/Panel/VBox/StatusLabel
@onready var streak_label: Label = $HUD/Margin/Panel/VBox/StreakLabel
@onready var count_label: Label = $HUD/Margin/Panel/VBox/CountLabel
@onready var hint_label: Label = $HUD/Margin/Panel/VBox/HintLabel
@onready var refresh_btn: Button = $HUD/Margin/Panel/VBox/RefreshBtn
@onready var toast: Label = $HUD/Toast
@onready var vignette: ColorRect = $HUD/Vignette

var _trees: Dictionary = {}  # milestone id -> StudyTree
var _active_tree: StudyTree = null
var _layout_seed: int = 42
var _toast_tween: Tween


func _ready() -> void:
	_setup_sky_shader()
	_setup_ambient_particles()
	_setup_hud()
	_fit_camera()

	GardenManager.garden_loaded.connect(_on_garden_loaded)
	GardenManager.garden_updated.connect(_on_garden_updated)
	GardenManager.garden_error.connect(_on_garden_error)
	GardenManager.tree_planted.connect(_on_tree_planted_signal)
	GardenManager.tree_bloomed.connect(_on_tree_bloomed_signal)
	GardenManager.tree_fruited.connect(_on_tree_fruited_signal)
	GardenManager.active_tree_wilted.connect(_on_active_wilted_signal)

	if not GardenManager.current_state.is_empty():
		_on_garden_loaded(GardenManager.current_state)
	else:
		status_label.text = "Growing your garden…"


func _setup_sky_shader() -> void:
	if sky and sky.material == null:
		var mat := ShaderMaterial.new()
		mat.shader = load("res://shaders/sky_gradient.gdshader")
		sky.material = mat
	# Fullscreen sky behind world
	if sky:
		sky.set_anchors_preset(Control.PRESET_FULL_RECT)
		sky.mouse_filter = Control.MOUSE_FILTER_IGNORE


func _setup_ambient_particles() -> void:
	if fireflies:
		fireflies.emitting = true
		fireflies.amount = 28
		fireflies.lifetime = 5.0
		fireflies.preprocess = 2.0
		fireflies.visibility_rect = Rect2(-700, -400, 1400, 800)
		var fm := ParticleProcessMaterial.new()
		fm.particle_flag_disable_z = true
		fm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
		fm.emission_box_extents = Vector3(520, 180, 1)
		fm.direction = Vector3(0, -0.2, 0)
		fm.spread = 180.0
		fm.initial_velocity_min = 4.0
		fm.initial_velocity_max = 14.0
		fm.gravity = Vector3(0, -2, 0)
		fm.scale_min = 0.15
		fm.scale_max = 0.4
		fm.color = Color("FFF59D")
		fireflies.process_material = fm
		fireflies.position = Vector2(0, -40)

	if pollen:
		pollen.emitting = true
		pollen.amount = 40
		pollen.lifetime = 8.0
		pollen.preprocess = 3.0
		pollen.visibility_rect = Rect2(-800, -500, 1600, 1000)
		var pm := ParticleProcessMaterial.new()
		pm.particle_flag_disable_z = true
		pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
		pm.emission_box_extents = Vector3(600, 220, 1)
		pm.direction = Vector3(0.4, 0.1, 0)
		pm.spread = 40.0
		pm.initial_velocity_min = 6.0
		pm.initial_velocity_max = 18.0
		pm.gravity = Vector3(2, 6, 0)
		pm.scale_min = 0.08
		pm.scale_max = 0.22
		pm.color = Color(1, 0.95, 0.85, 0.55)
		pollen.process_material = pm

	if warm_light:
		warm_light.color = Color(1.0, 0.9, 0.65)
		warm_light.energy = 0.75
		warm_light.texture_scale = 2.8
		warm_light.position = Vector2(280, -180)
		# PointLight2D requires a texture in Godot 4
		if warm_light.texture == null:
			warm_light.texture = _make_radial_light_texture(256)


func _setup_hud() -> void:
	if refresh_btn:
		refresh_btn.pressed.connect(func(): GardenManager.refresh())
	if toast:
		toast.modulate.a = 0.0
	if vignette and vignette.material == null:
		# Soft edge darken via modulate gradient is enough
		vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
		vignette.color = Color(0, 0, 0, 0)  # optional; can add shader later


func _make_radial_light_texture(size: int = 256) -> Texture2D:
	var img := Image.create(size, size, false, Image.FORMAT_RGBA8)
	var center := Vector2(size * 0.5, size * 0.5)
	var max_r := size * 0.5
	for y in size:
		for x in size:
			var d := Vector2(x, y).distance_to(center) / max_r
			var a := clampf(1.0 - d, 0.0, 1.0)
			a = a * a  # soft falloff
			img.set_pixel(x, y, Color(1, 1, 1, a))
	return ImageTexture.create_from_image(img)


func _fit_camera() -> void:
	if camera:
		camera.position = Vector2(0, -20)
		camera.zoom = Vector2(1.0, 1.0)
		# Slight settle zoom-in on start
		camera.zoom = Vector2(0.92, 0.92)
		var tw := create_tween()
		tw.tween_property(camera, "zoom", Vector2(1.0, 1.0), 1.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)


func _on_garden_loaded(state: Dictionary) -> void:
	_clear_trees()
	var milestones: Array = state.get("milestones", [])
	for i in milestones.size():
		var m: Dictionary = milestones[i]
		_spawn_tree(m, false, i)
	_sync_active_tree(state, false)
	_update_hud(state)
	status_label.text = "Garden ready"
	if milestones.is_empty():
		_show_toast("Your first tree grows after 4 days of ≥6h study 🌱")


func _on_garden_updated(state: Dictionary, new_ids: Array) -> void:
	var milestones: Array = state.get("milestones", [])
	var index_by_id := {}
	for i in milestones.size():
		index_by_id[int(milestones[i].get("id", -1))] = i

	# Update existing + plant new
	for m in milestones:
		var mid := int(m.get("id", -1))
		if _trees.has(mid):
			var tree: StudyTree = _trees[mid]
			var animate := mid in new_ids or _milestone_upgraded(tree.milestone, m)
			tree.configure_from_milestone(m, animate)
		else:
			var idx: int = index_by_id.get(mid, _trees.size())
			# Spawn at final state, then play plant pop so it doesn't double-tween growth
			var tree2 := _spawn_tree(m, false, idx)
			if mid in new_ids and tree2:
				await tree2.play_plant_celebration()
				_show_toast("New tree planted! Milestone #%d 🌳" % mid)

	# Remove trees no longer present (shouldn't happen for permanent milestones)
	var living_ids: Array = []
	for m2 in milestones:
		living_ids.append(int(m2.get("id", -1)))
	for id in _trees.keys():
		if id not in living_ids:
			var doomed: StudyTree = _trees[id]
			doomed.queue_free()
			_trees.erase(id)

	_sync_active_tree(state, true)
	_update_hud(state)
	status_label.text = "Synced"


func _milestone_upgraded(prev: Dictionary, next: Dictionary) -> bool:
	if not bool(prev.get("has_flowers", false)) and bool(next.get("has_flowers", false)):
		return true
	if not bool(prev.get("has_fruits", false)) and bool(next.get("has_fruits", false)):
		return true
	return false


func _on_garden_error(message: String) -> void:
	status_label.text = "Offline mode" if "mock" in message.to_lower() or GardenManager.use_mock_on_failure else "API issue"
	if "mock" in message.to_lower() or not GardenManager.current_state.is_empty():
		hint_label.text = "Showing local preview — start FastAPI for live data"
	else:
		hint_label.text = message


func _on_tree_planted_signal(milestone: Dictionary) -> void:
	_show_toast("🌳 Tree #%d planted — 4-day streak locked in!" % int(milestone.get("id", 0)))


func _on_tree_bloomed_signal(milestone: Dictionary) -> void:
	_show_toast("🌸 Tree #%d bloomed — cherry blossoms!" % int(milestone.get("id", 0)))


func _on_tree_fruited_signal(milestone: Dictionary) -> void:
	var score = milestone.get("test_score", null)
	var extra := " (%s%%)" % str(score) if score != null else ""
	_show_toast("🍎 Shiny fruit on tree #%d%s" % [int(milestone.get("id", 0)), extra])


func _on_active_wilted_signal() -> void:
	_show_toast("🍂 Active sprout wilted — past trees still thrive. Restart your streak!")


func _spawn_tree(milestone: Dictionary, animate: bool, index: int) -> StudyTree:
	var tree: StudyTree = StudyTreeScene.instantiate()
	trees_root.add_child(tree)
	var pos := slot_position(index, maxi(GardenManager.get_milestones().size(), index + 1))
	tree.position = pos
	# Depth sort: lower on screen draws in front
	tree.z_index = int(pos.y)
	var scale_var := 0.88 + fmod(float(int(milestone.get("id", index)) * 0.07), 0.22)
	tree.scale = Vector2(scale_var, scale_var)
	tree.configure_from_milestone(milestone, animate)
	_trees[int(milestone.get("id", index))] = tree
	return tree


func _sync_active_tree(state: Dictionary, animate: bool) -> void:
	var streak := int(state.get("current_streak_days", 0))
	var active: Dictionary = state.get("active_tree", {})
	var progress := int(active.get("progress_days", streak % 4))
	var wilted := bool(active.get("wilted", streak <= 0))

	# Show active sapling only when mid-cycle (1–3 days into next tree)
	var show_active := false
	if streak > 0:
		var rem := streak % 4
		show_active = rem != 0
		progress = rem if rem != 0 else 0
		wilted = false
	elif wilted and not _trees.is_empty():
		# Streak broken: show wilted active only if we were mid-progress
		# Prefer backend flag; if wilted true with 0 progress, still show a sad sapling
		show_active = true
		progress = max(progress, 1)

	if not show_active:
		if _active_tree:
			_active_tree.queue_free()
			_active_tree = null
		return

	if _active_tree == null:
		_active_tree = StudyTreeScene.instantiate()
		active_root.add_child(_active_tree)
		var next_index := _trees.size()
		_active_tree.position = slot_position(next_index, next_index + 1)
		_active_tree.z_index = int(_active_tree.position.y)
		_active_tree.modulate = Color(1, 1, 1, 0.95)

	_active_tree.configure_active(progress, wilted, animate)


func _update_hud(state: Dictionary) -> void:
	var streak := int(state.get("current_streak_days", 0))
	var count := (state.get("milestones", []) as Array).size()
	streak_label.text = "🔥 Streak  %d day%s" % [streak, "s" if streak != 1 else ""]
	count_label.text = "🌳 Grove  %d permanent tree%s" % [count, "s" if count != 1 else ""]

	var rem := streak % 4
	if streak <= 0:
		hint_label.text = "Hit ≥6h today to sprout the next tree. Past milestones stay forever."
	elif rem == 0:
		hint_label.text = "Milestone locked! Keep going — day 5–6 blooms cherry blossoms 🌸"
	elif rem >= 1 and streak < 4:
		hint_label.text = "Growing… %d / 4 days until a new permanent tree" % rem
	elif rem > 0:
		hint_label.text = "%d / 4 days into the next tree · 6-day streaks bloom 🌸 · >60%% tests fruit 🍎" % rem
	else:
		hint_label.text = "Your garden remembers every hard-won milestone."


func slot_position(index: int, total: int) -> Vector2:
	"""Organic orchard layout: golden-angle spiral with slight noise."""
	var n := maxi(total, 1)
	var golden := PI * (3.0 - sqrt(5.0))
	var t := float(index) + 0.5
	var r := SLOT_RADIUS * sqrt(t / float(maxi(n, 8))) * 1.15
	r = minf(r, SLOT_RADIUS * 1.05)
	var angle := index * golden + float(_layout_seed) * 0.01
	# Flatten into a clearing (ellipse)
	var pos := SLOT_CENTER + Vector2(cos(angle) * r * 1.25, sin(angle) * r * 0.62)
	# Deterministic jitter
	var rng := RandomNumberGenerator.new()
	rng.seed = index * 9176 + _layout_seed
	pos += Vector2(rng.randf_range(-12, 12), rng.randf_range(-8, 8))
	return pos


func _clear_trees() -> void:
	for id in _trees.keys():
		var t: StudyTree = _trees[id]
		if is_instance_valid(t):
			t.queue_free()
	_trees.clear()
	if _active_tree and is_instance_valid(_active_tree):
		_active_tree.queue_free()
	_active_tree = null


func _show_toast(text: String) -> void:
	if not toast:
		return
	toast.text = text
	if _toast_tween and _toast_tween.is_valid():
		_toast_tween.kill()
	toast.modulate.a = 0.0
	_toast_tween = create_tween()
	_toast_tween.tween_property(toast, "modulate:a", 1.0, 0.25)
	_toast_tween.tween_interval(2.6)
	_toast_tween.tween_property(toast, "modulate:a", 0.0, 0.5)


func _unhandled_input(event: InputEvent) -> void:
	# Gentle pan / zoom for exploration
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed and camera:
			if mb.button_index == MOUSE_BUTTON_WHEEL_UP:
				camera.zoom = (camera.zoom * 1.08).clamp(Vector2(0.65, 0.65), Vector2(1.6, 1.6))
			elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				camera.zoom = (camera.zoom / 1.08).clamp(Vector2(0.65, 0.65), Vector2(1.6, 1.6))
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_MIDDLE):
		var mm := event as InputEventMouseMotion
		if camera:
			camera.position -= mm.relative / camera.zoom
