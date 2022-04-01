import logging
from queue import Queue
from typing import Any

from app.overlay import overlay


class Update:
    def __init__(self, field: str, text: str=None, append=False, size=None, enable=None, visible=None) -> None:
        self.field = field
        self.text = text
        self.append = append
        self.size = size
        self.enable = enable
        self.visible = visible


class Event:
    def __init__(self, event_name, value) -> None:
        self.event_name = event_name
        self.value = value

    def fire(self) -> None:
        overlay.window.write_event_value(self.event_name, self.value)


class _OverlayUpdates:
    def __init__(self) -> None:
        self.updates = Queue()

    def update(self, field: str, text: str, append=False, size=None) -> None:
        try:
            overlay.updatetext(field, text, size, append)
        except RuntimeError:
            # we are in a different thread. queue the update.
            update = Update(field, text, append, size)
            self.updates.put(update)

    def enable(self, field: str, enable: bool = True) -> None:
        try:
            overlay.window[field].update(disabled=not enable)
        except RuntimeError:
            # we are in a different thread. queue the update.
            update = Update(field, enable=enable)
            self.updates.put(update)

    def visible(self, field, visible: bool = True, size=None):
        try:
            overlay.window[field].update(visible=visible)
            if size:
                overlay.window[field].set_size(size)
        except RuntimeError:
            # we are in a different thread. queue the update.
            update = Update(field, visible=visible, size=size)
            self.updates.put(update)

    def disable(self, field: str) -> None:
        return self.enable(field, False)

    def clear(self) -> None:
        field_list = [
            'elapsed',
            'key_count',
            'ocr_count',
            'accuracy',
            'listings_count',
            'p_fails',
            'rejects',
            'log_output',
            'error_output'
        ]
        for field in field_list:
            OverlayUpdateHandler.update(field, '')

    def fire_event(self, event: str, with_value: Any = None) -> None:
        event = Event(event, with_value)
        try:
            event.fire()
        except RuntimeError:
            self.updates.append(event)

    def flush_updates(self) -> None:
        while self.updates.qsize() > 0:
            update = self.updates.get()
            if isinstance(update, Event):
                update.fire()
            if update.enable is not None:
                overlay.window[update.field].update(disabled=not update.enable)
            elif update.visible is not None:
                overlay.window[update.field].update(visible=update.visible)
            else:
                overlay.updatetext(update.field, update.text, update.size, update.append)


OverlayUpdateHandler = _OverlayUpdates()
