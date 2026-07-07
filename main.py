"""Flet build entry point — delegates to the mobile app."""

from mobile.main import main

if __name__ == "__main__":
    import flet as ft

    ft.app(target=main)