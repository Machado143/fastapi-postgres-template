import logging
import sys

from pythonjsonlogger import jsonlogger

import contextvars

request_id_ctx_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
user_id_ctx_var: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "user_id", default=None
)


class ContextFilter(logging.Filter):
    """Injects request_id and user_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx_var.get()
        record.user_id = user_id_ctx_var.get()
        return True


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    fmt = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s " "%(message)s %(request_id)s %(user_id)s"
    )
    handler.setFormatter(fmt)
    handler.addFilter(ContextFilter())

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


logger = logging.getLogger("app")
