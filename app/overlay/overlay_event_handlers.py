def popup_keybinds() -> None:
    from app.overlay import overlay
    from app.overlay.layouts.key_settings_layout import settings_layout
    overlay.popup_window(settings_layout())


def popup_sections() -> None:
    from app.overlay import overlay
    from app.overlay.layouts.scan_options_layout import sections_layout
    overlay.popup_window(sections_layout())
