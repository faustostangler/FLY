from __future__ import annotations

import inspect
from pathlib import Path


class ContextTracker:
    """Utilities to extract caller context for debugging/logging.

    This helper inspects the Python call stack to produce:
    - A concise textual breadcrumb of where a call originated in the project.
    - A fully qualified import path for the calling function or bound method.

    Args:
        project_root (Path): Absolute path that bounds the project. Only stack
            frames whose files live under this directory are considered when
            building human-readable context strings.
    """

    def __init__(self, project_root: Path) -> None:
        # Store the root directory used to filter relevant frames
        self.project_root = project_root

    def get_context(self) -> str:
        """Build a left-to-right breadcrumb of project-relevant stack frames.

        Returns:
            str: A compact string like
                ``"line 42 of fetch() in 'src/client.py' <- line 10 of run() in 'main.py'"``.
                Returns an empty string if the context cannot be determined.
        """
        # Attempt to walk the current call stack and keep only project frames
        try:
            # Capture the live stack frames (most recent first)
            stack = inspect.stack()

            # Accumulate formatted fragments for frames under project_root
            relevant = []

            # Iterate through the stack to find frames within project boundaries
            for frame in stack:
                path = Path(frame.filename).resolve()
                if self.project_root in path.parents:
                    # Compute the path relative to the project root for readability
                    rel_path = path.relative_to(self.project_root)

                    # Record a readable snippet for the current frame
                    relevant.append(
                        f"line {frame.lineno} of {frame.function}() in '{rel_path}'"
                    )

            # Skip the current helper frames and join remaining parts
            return " <- ".join(relevant[3:-1])
        except Exception:
            # On any inspection error, fall back to an empty context
            return ""

    def get_import_path(self) -> str:
        """Return the fully qualified import path of the immediate caller.

        The result includes the module and, when applicable, the class
        that owns the bound method.

        Returns:
            str: A path in the format ``"package.module.Class.method"`` or
            ``"package.module.function"``. Returns ``"<unknown>"`` if it
            cannot be determined.
        """
        # Use a local import to mirror the original pattern and isolate scope
        import inspect

        # Try to resolve the module and class/function for the caller frame
        try:
            # Collect the stack and skip frames belonging to this helper
            stack = inspect.stack()

            # Start at index 2 to jump over this method and its direct caller
            for frame_info in stack[2:]:
                # Extract the frame object for inspection
                frame = frame_info.frame

                # Get the function name from the code object
                func = frame.f_code.co_name

                # Attempt to resolve a bound class from the frame (e.g., methods)
                cls = self._get_class_from_frame(frame)

                # If a class is found, build Class.method fully qualified path
                if cls is not None:
                    module = inspect.getmodule(cls)
                    mod = module.__name__ if module else cls.__module__
                    return f"{mod}.{cls.__name__}.{func}"

                # Otherwise, fall back to module-level function path
                else:
                    module = inspect.getmodule(frame)
                    mod = module.__name__ if module else "<unknown>"
                    return f"{mod}.{func}"

            # If the stack was too shallow or no frame matched, return sentinel
            return "<unknown>"
        except Exception:
            # On any error during inspection, return sentinel
            return "<unknown>"

    def _get_class_from_frame(self, frame) -> type | None:
        """Infer the class of a bound method from a frame, if available.

        Heuristic:
            If the first local argument resembles a bound instance (commonly
            named ``self``), return its class. Otherwise return ``None``.

        Args:
            frame: A Python frame object to inspect.

        Returns:
            type | None: The resolved class for the bound method, or ``None`` if
            the frame does not appear to belong to an instance method.
        """
        # Retrieve argument names and local variables for the given frame
        args, _, _, local_vars = inspect.getargvalues(frame)

        # Check whether the first arg looks like a bound instance (e.g., "self")
        if args:
            self_obj = local_vars.get(args[0], None)

            # Use a permissive check to cover most user-defined objects
            if isinstance(self_obj, object):
                return self_obj.__class__

        # If no instance-like first arg is present, this is likely a function
        return None
