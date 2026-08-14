extends Node2D
## Soft rolling meadow + path for the garden clearing.

@export var meadow_color: Color = Color("4CAF50")
@export var deep_grass: Color = Color("2E7D32")
@export var soil_color: Color = Color("6D4C41")
@export var path_color: Color = Color("A1887F")
@export var highlight: Color = Color("81C784")


func _ready() -> void:
	queue_redraw()
	z_index = -10


func _draw() -> void:
	# Large soft ground ellipse (clearing)
	_fill_ellipse(Vector2(0, 90), 620, 220, deep_grass.darkened(0.15))
	_fill_ellipse(Vector2(0, 70), 560, 190, meadow_color.darkened(0.05))
	_fill_ellipse(Vector2(-40, 50), 420, 150, meadow_color.lightened(0.06))

	# Dirt path winding through the grove
	var path := PackedVector2Array([
		Vector2(-480, 120), Vector2(-300, 100), Vector2(-120, 90),
		Vector2(40, 100), Vector2(200, 85), Vector2(380, 110), Vector2(520, 130)
	])
	draw_polyline(path, path_color.darkened(0.1), 38.0, true)
	draw_polyline(path, path_color.lightened(0.08), 22.0, true)

	# Soft soil patches
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	for i in 18:
		var p := Vector2(rng.randf_range(-480, 480), rng.randf_range(20, 160))
		_fill_ellipse(p, rng.randf_range(12, 28), rng.randf_range(6, 12), soil_color.lerp(meadow_color, 0.55))

	# Grass tufts
	for i in 40:
		var x := rng.randf_range(-500, 500)
		var y := rng.randf_range(10, 170)
		var h := rng.randf_range(6, 14)
		var c := highlight.lerp(deep_grass, rng.randf())
		draw_line(Vector2(x, y), Vector2(x - 2, y - h), c, 1.5)
		draw_line(Vector2(x, y), Vector2(x + 3, y - h * 0.85), c.lightened(0.1), 1.3)

	# Far hedge / jungle edge silhouettes
	var hedge := Color("1B5E20").darkened(0.25)
	hedge.a = 0.55
	for i in 12:
		var hx := -560 + i * 100.0 + rng.randf_range(-20, 20)
		_fill_ellipse(Vector2(hx, -10), 70, 48, hedge)
		_fill_ellipse(Vector2(hx + 30, -30), 50, 40, hedge.lightened(0.05))


func _fill_ellipse(center: Vector2, rx: float, ry: float, color: Color, segs: int = 28) -> void:
	var pts := PackedVector2Array()
	for i in segs:
		var a := TAU * float(i) / float(segs)
		pts.append(center + Vector2(cos(a) * rx, sin(a) * ry))
	draw_colored_polygon(pts, color)
