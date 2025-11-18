import inspect
from pathlib import Path


class ContextTracker:
    """Extracts the call origin within the project for debugging logs."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def get_context(self) -> str:
        """Return a string like ``"line X of func() in 'path/file.py' <-
        ..."``."""
        try:
            stack = inspect.stack()
            relevant = []

            for frame in stack:
                path = Path(frame.filename).resolve()
                if self.project_root in path.parents:
                    rel_path = path.relative_to(self.project_root)
                    relevant.append(
                        f"line {frame.lineno} of {frame.function}() in '{rel_path}'"
                    )

            return " <- ".join(relevant[3:-1])
        except Exception:
            return ""

    def get_import_path(self) -> str:
        """Return the fully qualified import path of the caller method."""
        import inspect

        try:
            stack = inspect.stack()
            for frame_info in stack[2:]:
                frame = frame_info.frame
                func = frame.f_code.co_name
                cls = self._get_class_from_frame(frame)
                if cls is not None:
                    module = inspect.getmodule(cls)
                    mod = module.__name__ if module else cls.__module__
                    return f"{mod}.{cls.__name__}.{func}"
                else:
                    module = inspect.getmodule(frame)
                    mod = module.__name__ if module else "<unknown>"
                    return f"{mod}.{func}"
            return "<unknown>"
        except Exception:
            return "<unknown>"

    def _get_class_from_frame(self, frame) -> type | None:
        args, _, _, local_vars = inspect.getargvalues(frame)
        if args:
            self_obj = local_vars.get(args[0], None)
            if isinstance(self_obj, object):
                return self_obj.__class__
        return None
