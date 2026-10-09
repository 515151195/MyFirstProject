import logging
import sys

from .context import get_request_id

class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True

class PlainFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        line = (
            f"{timestamp} "
            f"| {record.levelname:<8} "
            f"| request_id={getattr(record, 'request_id', '-')} "
            f"| {record.name} "
            f"| {record.getMessage()}"
        )
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def set_up_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(PlainFormatter())

    file_handler = logging.FileHandler("app.log", mode="w", encoding="utf-8")
    file_handler.addFilter(RequestIdFilter())
    handler.setFormatter(PlainFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(level)

    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

logger = logging.getLogger()