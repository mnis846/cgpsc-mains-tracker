"""Shim — import from app_styles to avoid clashing with other projects' styles.py."""

from app_styles import APP_CSS, DEFAULT_THEME, THEME_OPTIONS, get_app_css, resolve_theme

__all__ = ["APP_CSS", "DEFAULT_THEME", "THEME_OPTIONS", "get_app_css", "resolve_theme"]
