extends Node
## Autoload singleton: fetches garden state from FastAPI and broadcasts changes.
##
## Expected JSON (GET /api/garden/milestones):
## {
##   "current_streak_days": 5,
##   "milestones": [
##     {"id": 1, "achieved_date": "2026-07-10", "has_flowers": true,
##      "has_fruits": true, "test_score": 72}
##   ],
##   "active_tree": {"progress_days": 1, "wilted": false}  # optional
## }

signal garden_loaded(state: Dictionary)
signal garden_updated(state: Dictionary, new_milestone_ids: Array)
signal garden_error(message: String)
signal tree_planted(milestone: Dictionary)
signal tree_bloomed(milestone: Dictionary)
signal tree_fruited(milestone: Dictionary)
signal active_tree_wilted()

## Base URL of the FastAPI backend (no trailing slash).
@export var api_base_url: String = "http://127.0.0.1:8000"
## Path to the milestones endpoint.
@export var milestones_path: String = "/api/garden/milestones"
## Poll interval in seconds (0 = fetch only on startup / manual refresh).
@export var poll_interval_sec: float = 12.0
## When true (or API fails), load res://data/mock_garden.json so the garden still looks good.
@export var use_mock_on_failure: bool = true
## Force mock data even when the API is reachable (useful for art polish).
@export var force_mock: bool = false

var current_state: Dictionary = {}
var known_milestone_ids: Dictionary = {}  # id -> snapshot dict
var is_loading: bool = false
var last_error: String = ""

var _http: HTTPRequest
var _poll_timer: Timer
var _request_kind: String = ""  # "full" | ""


func _ready() -> void:
	_http = HTTPRequest.new()
	_http.timeout = 8.0
	_http.request_completed.connect(_on_request_completed)
	add_child(_http)

	_poll_timer = Timer.new()
	_poll_timer.wait_time = maxf(poll_interval_sec, 3.0)
	_poll_timer.one_shot = false
	_poll_timer.autostart = false
	_poll_timer.timeout.connect(refresh)
	add_child(_poll_timer)

	# Allow runtime override from environment / OS args
	_apply_cli_overrides()
	call_deferred("refresh")


func _apply_cli_overrides() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--api="):
			api_base_url = arg.substr(6).rstrip("/")
		elif arg == "--mock":
			force_mock = true
		elif arg.begins_with("--poll="):
			poll_interval_sec = float(arg.substr(7))
			_poll_timer.wait_time = maxf(poll_interval_sec, 3.0)


func set_api_url(url: String) -> void:
	api_base_url = url.rstrip("/")


func refresh() -> void:
	if is_loading:
		return
	if force_mock:
		_load_mock("forced mock mode")
		return
	_request_garden()


func get_milestones() -> Array:
	return current_state.get("milestones", [])


func get_streak() -> int:
	return int(current_state.get("current_streak_days", 0))


func get_active_tree() -> Dictionary:
	return current_state.get("active_tree", {})


func is_active_wilted() -> bool:
	var active: Dictionary = get_active_tree()
	if active.is_empty():
		# Infer: no live streak and no explicit active tree → wilted in-progress
		return get_streak() <= 0 and not known_milestone_ids.is_empty()
	return bool(active.get("wilted", false))


func _request_garden() -> void:
	is_loading = true
	_request_kind = "full"
	var url := api_base_url.rstrip("/") + milestones_path
	var headers := PackedStringArray(["Accept: application/json"])
	var err := _http.request(url, headers, HTTPClient.METHOD_GET)
	if err != OK:
		is_loading = false
		_handle_failure("HTTPRequest failed to start (err %d)" % err)


func _on_request_completed(
	result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray
) -> void:
	is_loading = false
	if result != HTTPRequest.RESULT_SUCCESS or response_code < 200 or response_code >= 300:
		_handle_failure("API error result=%d code=%d" % [result, response_code])
		return
	var text := body.get_string_from_utf8()
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		_handle_failure("Invalid JSON from garden API")
		return
	_apply_state(parsed as Dictionary, false)


func _handle_failure(message: String) -> void:
	last_error = message
	push_warning("[GardenManager] %s" % message)
	garden_error.emit(message)
	if use_mock_on_failure and current_state.is_empty():
		_load_mock(message)
	elif poll_interval_sec > 0.0 and not _poll_timer.is_stopped():
		pass  # keep polling
	_ensure_polling()


func _load_mock(reason: String) -> void:
	var path := "res://data/mock_garden.json"
	if not FileAccess.file_exists(path):
		garden_error.emit("Mock data missing and API unavailable: %s" % reason)
		return
	var f := FileAccess.open(path, FileAccess.READ)
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		garden_error.emit("Corrupt mock_garden.json")
		return
	print("[GardenManager] Using mock garden (%s)" % reason)
	_apply_state(parsed as Dictionary, true)
	_ensure_polling()


func _apply_state(state: Dictionary, from_mock: bool) -> void:
	state = _normalize_state(state)
	var first_load := current_state.is_empty()
	var new_ids: Array = []
	var milestones: Array = state.get("milestones", [])

	for m in milestones:
		if typeof(m) != TYPE_DICTIONARY:
			continue
		var mid: int = int(m.get("id", -1))
		if mid < 0:
			continue
		if not known_milestone_ids.has(mid):
			if not first_load:
				new_ids.append(mid)
				tree_planted.emit(m)
			known_milestone_ids[mid] = m.duplicate(true)
		else:
			var prev: Dictionary = known_milestone_ids[mid]
			if not bool(prev.get("has_flowers", false)) and bool(m.get("has_flowers", false)):
				tree_bloomed.emit(m)
			if not bool(prev.get("has_fruits", false)) and bool(m.get("has_fruits", false)):
				tree_fruited.emit(m)
			known_milestone_ids[mid] = m.duplicate(true)

	var prev_wilted := is_active_wilted() if not first_load else false
	current_state = state

	if not first_load:
		var now_wilted := is_active_wilted()
		if now_wilted and not prev_wilted:
			active_tree_wilted.emit()
		garden_updated.emit(state, new_ids)
	else:
		garden_loaded.emit(state)

	if from_mock:
		last_error = ""
	_ensure_polling()


func _normalize_state(state: Dictionary) -> Dictionary:
	var out := state.duplicate(true)
	if not out.has("current_streak_days"):
		out["current_streak_days"] = 0
	if not out.has("milestones") or typeof(out["milestones"]) != TYPE_ARRAY:
		out["milestones"] = []

	# Sort milestones by id / date for stable planting order
	var ms: Array = out["milestones"]
	ms.sort_custom(func(a, b): return int(a.get("id", 0)) < int(b.get("id", 0)))
	out["milestones"] = ms

	# Derive active tree if backend omitted it
	if not out.has("active_tree") or typeof(out["active_tree"]) != TYPE_DICTIONARY:
		var streak := int(out["current_streak_days"])
		var progress := streak % 4
		if streak > 0 and progress == 0:
			# Exactly on a 4-day boundary — active slot is the newest permanent tree
			progress = 0
		out["active_tree"] = {
			"progress_days": progress if streak > 0 else 0,
			"wilted": streak <= 0 and ms.size() > 0,
		}
	return out


func _ensure_polling() -> void:
	if poll_interval_sec <= 0.0:
		_poll_timer.stop()
		return
	_poll_timer.wait_time = maxf(poll_interval_sec, 3.0)
	if _poll_timer.is_stopped():
		_poll_timer.start()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("refresh_garden"):
		refresh()
