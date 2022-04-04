import logging
from datetime import datetime
from tkinter import TclError

from app.overlay.overlay_updates import OverlayUpdateHandler
from app.settings import SETTINGS


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
        except TclError:
            pass
        except:
            self.handleError(record)

    @classmethod
    def setup_overlay_logging(cls):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(SETTINGS.console_logging_level)

        target_dir = SETTINGS.app_data_sub_path("logging")
        target_file = target_dir / datetime.now().strftime("%Y%m%d_%H%M%S.log.txt")
        file_handler = logging.FileHandler(target_file, mode="w")
        file_handler.setLevel(logging.DEBUG)

        overlay_handler = cls()
        overlay_handler.setLevel(logging.INFO)

        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(levelname)s] %(message)s",
            handlers=[
                stream_handler,
                overlay_handler,
                file_handler
            ]
        )

        logging.info(f"Logging file created at `{target_file}`")
