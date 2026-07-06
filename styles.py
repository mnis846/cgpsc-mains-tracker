"""Shim — import from app_styles to avoid clashing with other projects' styles.py."""

from app_styles import APP_CSS

__all__ = ["APP_CSS"]