shader_type canvas_item;

uniform vec4 top_color : source_color = vec4(0.42, 0.68, 0.92, 1.0);
uniform vec4 mid_color : source_color = vec4(0.78, 0.90, 0.96, 1.0);
uniform vec4 bottom_color : source_color = vec4(0.96, 0.90, 0.72, 1.0);
uniform float mid_stop : hint_range(0.0, 1.0) = 0.45;
uniform float sun_y : hint_range(0.0, 1.0) = 0.22;
uniform float sun_x : hint_range(0.0, 1.0) = 0.78;
uniform float sun_radius : hint_range(0.01, 0.5) = 0.12;
uniform vec4 sun_color : source_color = vec4(1.0, 0.92, 0.55, 1.0);
uniform float god_ray_strength : hint_range(0.0, 1.0) = 0.35;
uniform float time_scale : hint_range(0.0, 2.0) = 0.15;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	float t = UV.y;
	vec3 col;
	if (t < mid_stop) {
		col = mix(top_color.rgb, mid_color.rgb, t / max(mid_stop, 0.001));
	} else {
		col = mix(mid_color.rgb, bottom_color.rgb, (t - mid_stop) / max(1.0 - mid_stop, 0.001));
	}

	// Soft sun disc + glow
	vec2 sun_pos = vec2(sun_x, sun_y);
	float d = distance(UV, sun_pos);
	float sun_core = smoothstep(sun_radius, sun_radius * 0.35, d);
	float sun_halo = exp(-d * d * 28.0) * 0.85;
	col = mix(col, sun_color.rgb, sun_core * 0.95);
	col += sun_color.rgb * sun_halo * 0.55;

	// Animated god rays from the sun
	vec2 ray_dir = normalize(UV - sun_pos + vec2(0.0001));
	float angle = atan(ray_dir.y, ray_dir.x);
	float rays = sin(angle * 14.0 + TIME * time_scale) * 0.5 + 0.5;
	rays *= sin(angle * 7.0 - TIME * time_scale * 0.7) * 0.5 + 0.5;
	float ray_mask = smoothstep(0.02, 0.55, d) * (1.0 - smoothstep(0.55, 1.2, d));
	col += sun_color.rgb * rays * ray_mask * god_ray_strength * 0.35;

	// Subtle atmospheric noise
	float n = hash(UV * 40.0 + TIME * 0.02) * 0.015;
	col += n;

	COLOR = vec4(col, 1.0);
}
