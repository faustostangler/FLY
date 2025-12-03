from __future__ import annotations

import logging
from typing import Any, Mapping, MutableMapping, Optional

# from domain.ports.logger_ports import LoggerPort
from infrastructure.config.config_adapter import ConfigAdapter
from infrastructure.logging.context_tracker import ContextTracker
from infrastructure.logging.progress_formatter import ProgressFormatter
from infrastructure.utils.id_generator import IdGenerator


class Logger:
    """Application logger with contextual metadata and progress formatting.

    Wraps the standard `logging` API to consistently include a `run_id`,
    `worker_id`, contextual trace information, and optional progress details.

    Attributes:
        config (ConfigAdapter): Centralized application configuration.
        logger_name (str): Name of the underlying logger.
        progress_formatter (ProgressFormatter): Formats progress dicts.
        context_tracker (ContextTracker): Extracts import path and debug context.
        id_generator (IdGenerator): Generates stable run/worker identifiers.
        _run_id (str): Unique id for the current run/session.
        worker_id (str): Unique id for the current worker within the run.
        _logger (logging.LoggerAdapter): Configured logger adapter instance.
    """

    def __init__(
        self,
        config: ConfigAdapter,
        level: str = "DEBUG",
        logger_name: Optional[str] = None,
    ) -> None:
        """Initialize the logger and set up handlers/formatters.

        Args:
            config: Global configuration adapter.
            level: Minimum console logging level (e.g., "INFO", "DEBUG").
            logger_name: Optional explicit logger name. Defaults to app name or "FLY".
        """
        # Keep a reference to global configuration
        self.config = config

        # Resolve logger name from config or fallback
        self.logger_name = logger_name or self.config.fly_settings.app_name or "FLY"

        # Prepare helpers for progress formatting and contextual information
        self.progress_formatter = ProgressFormatter()
        self.context_tracker = ContextTracker(config.paths.root_dir)

        # Generate stable run and worker identifiers
        self.id_generator = IdGenerator(
            config=self.config, logger_name=self.logger_name
        )
        self._run_id = self.id_generator.create_id(size=8, random=True)
        self.worker_id = self.id_generator.create_id(size=8)

        # Build the configured LoggerAdapter instance
        self._logger = self._setup_logger(level)

    def _setup_logger(self, level: str) -> logging.LoggerAdapter:
        """Create and configure the base logger and attach handlers.

        Sets a stream handler for console output with the requested level,
        and a file handler for verbose logs. Both share a `SafeFormatter`
        that guarantees `run_id` and `worker_id` fields are present.

        Args:
            level: Console log level name (e.g., "INFO", "DEBUG").

        Returns:
            logging.LoggerAdapter: Logger adapter with default `run_id` context.
        """
        # Resolve log file path and obtain/create the named logger
        log_path = self.config.logging.full_path
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(logging.DEBUG)

        # Avoid duplicate handlers if called multiple times under same name
        if not logger.hasHandlers():
            # Create a formatter that injects missing fields safely
            formatter = SafeFormatter(
                "%(run_id)s %(worker_id)s %(asctime)s %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            # Configure console handler with requested level
            sh = logging.StreamHandler()
            sh.setLevel(getattr(logging, level.upper(), logging.INFO))
            sh.setFormatter(formatter)
            logger.addHandler(sh)

            # Configure file handler for full debug output
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        # Provide a base `run_id` via the adapter's `extra`
        adapter = MergedLoggerAdapter(logger, extra={"run_id": self._run_id})

        return adapter

    def log(
        self,
        message: str,
        level: str = "info",
        progress: Optional[Mapping[str, Any]] = None,
        extra: Optional[Mapping[str, Any]] = None,
        worker_id: Optional[str] = None,
        show_path: Optional[bool] = None,
    ) -> None:
        """Log a message with optional progress, context, and import-path info.

        Args:
            message: Core log text.
            level: Logging level name (e.g., "debug", "info", "warning", "error").
            progress: Optional dict representing progress to render inline.
            extra: Optional mapping of additional fields to append as text.
            worker_id: Optional override for the `worker_id` used in the record.
            show_path: If True, include the call-site import path; if False, omit it;
                if None, fall back to the configuration default.

        Raises:
            Exception: Not raised directly; any internal error falls back to an
                error log and the original message is preserved.
        """
        # Decide whether to show the import path for this call
        if show_path is True:
            import_path = self.context_tracker.get_import_path()
        elif show_path is False:
            import_path = ""
        else:
            # Use the config-defined default when not explicitly specified
            import_path = (
                self.context_tracker.get_import_path()
                if self.config.logging.show_path
                else ""
            )

        # Compose optional context and progress sections
        context_msg = (
            self.context_tracker.get_context() if level.lower() == "debug" else ""
        )
        progress_msg = self.progress_formatter.format(progress) if progress else ""

        # Assemble the full message with optional parts
        full_message = message
        if progress_msg:
            full_message += f" | {progress_msg}"
        if context_msg:
            full_message += f" | {context_msg}"
        if import_path:
            full_message = f"{full_message}\n{import_path}"

        # Append any ad-hoc extra fields as a compact string
        if extra:
            extra_str = " ".join(str(v) for v in extra.values() if v not in (None, ""))
            full_message += f" | {extra_str}"

        # Perform the actual logging with merged contextual `extra`
        try:
            log_fn = getattr(self._logger, level.lower(), self._logger.info)
            merged_extra = {
                "run_id": self._run_id,
                "worker_id": worker_id or self.worker_id,
            }
            log_fn(full_message, extra=merged_extra)
        except Exception as e:
            # Fallback on failure to avoid dropping the original message
            self._logger.error(f"Logging failed: {e} - {full_message}")


class SafeFormatter(logging.Formatter):
    """Formatter that guarantees presence of contextual fields.

    Ensures `run_id` and `worker_id` are always present on the record,
    injecting default values when missing before delegating to base formatting.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Provide default values for required contextual fields
        defaults = {
            "run_id": "0",
            "worker_id": "0",
        }

        # Inject defaults when attributes are absent or falsy
        for key, default in defaults.items():
            if not hasattr(record, key) or not getattr(record, key):
                setattr(record, key, default)

        return super().format(record)


class MergedLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that merges call-time `extra` with adapter defaults.

    When a log call supplies an `extra` mapping, it is merged with the
    adapter's base `extra`. Call-time keys override base keys.
    """

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, MutableMapping[str, Any]]:
        """Merge `extra` dicts and return the message/kwargs pair.

        Args:
            msg: The original log message string.
            kwargs: Keyword arguments passed to the underlying logger.

        Returns:
            tuple[str, MutableMapping[str, Any]]: The message and updated kwargs
            with a merged `extra` mapping.
        """
        # Normalize base and call-time `extra` to dictionaries
        base = self.extra if isinstance(self.extra, dict) else {}
        extra = kwargs.get("extra") or {}
        if not isinstance(extra, dict):
            extra = {}

        # Merge with call-time values taking precedence
        kwargs["extra"] = {**base, **extra}
        return (msg, kwargs)
