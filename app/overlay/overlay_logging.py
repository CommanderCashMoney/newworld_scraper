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
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler(),
                cls()
            ]
        )
        target_dir = SETTINGS.app_data_sub_path("logging")
        target_file = target_dir / datetime.now().strftime("%Y%m%d_%H%M%S.log.txt")

        handler = logging.FileHandler(target_file, mode="w")
        handler.setLevel(logging.DEBUG)
        logging.root.addHandler(handler)
        logging.info(f"Logging file created at `{target_file}`")
