import logging

from app.overlay.overlay_updates import OverlayUpdateHandler


class OverlayLoggingHandler(logging.Handler):
    def emit(self, record):
        func_map = {
            "DEBUG": "log",
            "INFO": "log",
            "WARNING": "log",
            "ERROR": "error",
            "CRITICAL": "error"
        }
        output_to = f"{func_map[record.levelname]}_output"
        try:
            msg = self.format(record)
            OverlayUpdateHandler.update(output_to, msg, True)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    @classmethod
    def setup_overlay_logging(cls):
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler(),
                cls()
            ]
        )
