extends Node2D
## Background / midground silhouettes for depth (distant trees, rocks, pond).


func _ready() -> void:
	z_index = -5
	queue_redraw()


func _draw() -> void:
	# Distant tree silhouettes
	var far := Color(0.12, 0.28, 0.16, 0.55)
	var mid := Color(0.15, 0.35, 0.18, 0.7)
	_tree_sil(Vector2(-420, 10), 1.4, far)
	_tree_sil(Vector2(-340, 5), 1.1, far)
	_tree_sil(Vector2(390, 8), 1.3, far)
	_tree_sil(Vector2(470, 15), 1.0, far)
	_tree_sil(Vector2(-500, 25), 0.9, mid)
	_tree_sil(Vector2(520, 28), 0.95, mid)

	# Small pond
	var pond_c := Color(0.35, 0.62, 0.78, 0.55)
	_ellipse(Vector2(300, 95), 55, 18, pond_c)
	_ellipse(Vector2(300, 92), 40, 10, Color(0.7, 0.88, 0.95, 0.35))

	# Rocks
	var rock := Color(0.45, 0.42, 0.38, 0.85)
	_ellipse(Vector2(-260, 110), 16, 9, rock)
	_ellipse(Vector2(-245, 112), 10, 7, rock.lightened(0.1))
	_ellipse(Vector2(180, 120), 14, 8, rock)

	# Flower patches on ground
	var rng := RandomNumberGenerator.new()
	rng.seed = 88
	for i in 24:
		var p := Vector2(rng.randf_range(-400, 400), rng.randf_range(40, 140))
		var c := Color("F8BBD0") if rng.randf() > 0.5 else Color("FFF59D")
		c.a = 0.75
		draw_circle(p, 2.0 + rng.randf() * 1.5, c)


func _tree_sil(pos: Vector2, s: float, color: Color) -> void:
	draw_colored_polygon(PackedVector2Array([
		pos + Vector2(-4, 0) * s, pos + Vector2(4, 0) * s,
		pos + Vector2(3, -40) * s, pos + Vector2(-3, -40) * s
	]), color.darkened(0.2))
	_ellipse(pos + Vector2(0, -55) * s, 28 * s, 22 * s, color)
	_ellipse(pos + Vector2(-14, -40) * s, 16 * s, 14 * s, color)
	_ellipse(pos + Vector2(14, -42) * s, 15 * s, 13 * s, color)


func _ellipse(center: Vector2, rx: float, ry: float, color: Color, segs: int = 16) -> void:
	var pts := PackedVector2Array()
	for i in segs:
		var a := TAU * float(i) / float(segs)
		pts.append(center + Vector2(cos(a) * rx, sin(a) * ry))
	draw_colored_polygon(pts, color)
