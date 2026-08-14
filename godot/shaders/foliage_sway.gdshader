shader_type canvas_item;

uniform float sway_strength : hint_range(0.0, 0.08) = 0.018;
uniform float sway_speed : hint_range(0.0, 4.0) = 1.1;
uniform float phase_offset : hint_range(0.0, 6.28) = 0.0;
uniform float wilt_amount : hint_range(0.0, 1.0) = 0.0;
uniform vec4 healthy_tint : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform vec4 wilt_tint : source_color = vec4(0.82, 0.72, 0.28, 1.0);

void vertex() {
	float height_factor = 1.0 - UV.y; // sway more at the top
	float wave = sin(TIME * sway_speed + phase_offset + VERTEX.y * 0.04);
	float wilt_droop = wilt_amount * height_factor * 8.0;
	VERTEX.x += wave * sway_strength * 40.0 * height_factor * (1.0 - wilt_amount * 0.6);
	VERTEX.y += wilt_droop + abs(wave) * sway_strength * 6.0 * wilt_amount;
}

void fragment() {
	vec4 tex = texture(TEXTURE, UV);
	vec4 tint = mix(healthy_tint, wilt_tint, wilt_amount);
	COLOR = tex * tint * COLOR;
}
