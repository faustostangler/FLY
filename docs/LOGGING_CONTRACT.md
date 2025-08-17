# Logging Contract

Logging is handled by `infrastructure.logging.Logger`. Use `logger.log()` instead of `print()`.

- Log the start and end of every major step.
- Log retries or errors with `level="warning"` or `level="error"`.
- Include progress information where available (`progress={}`).
- The default format includes `run_id` and `worker_id` for traceability.
- Log level defaults to `DEBUG` in development and `INFO` in production.
- When using thread pools, pass the worker ID to preserve context.
