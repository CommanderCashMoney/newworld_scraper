from queue import Queue

from app.overlay import overlay


class Update:
    def __init__(self, field: str, text: str=None, append=False, size=None, enable=None) -> None:
        self.field = field
        self.text = text
        self.append = append
        self.size = size
        self.enable = enable


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

    def flush_updates(self) -> None:
        while self.updates.qsize() > 0:
            update = self.updates.get()
            if update.enable is not None:
                overlay.window[update.field].update(disabled=not update.enable)
            else:
                overlay.updatetext(update.field, update.text, update.size, update.append)


OverlayUpdateHandler = _OverlayUpdates()
