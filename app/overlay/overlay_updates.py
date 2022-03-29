from queue import Queue

from app.overlay import overlay


class Update:
    def __init__(self, field: str, text: str, append=False, size=None) -> None:
        self.field = field
        self.text = text
        self.append = append
        self.size = size


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

    def flush_updates(self) -> None:
        while self.updates.qsize() > 0:
            update = self.updates.get()
            overlay.updatetext(update.field, update.text, update.size, update.append)


OverlayUpdateHandler = _OverlayUpdates()
