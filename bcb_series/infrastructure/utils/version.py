from __future__ import annotations

import os
import shutil
import subprocess
import sys
from functools import lru_cache
from typing import List, Optional


def _git_available() -> bool:
    """Check whether the `git` executable is available in PATH.

    Returns:
        bool: True if `git` is found, otherwise False.
    """
    # Ask system PATH for a `git` binary
    return shutil.which("git") is not None


def _run_git(args: List[str], timeout: float = 2.0) -> Optional[str]:
    """Run a git command and return its stdout as a decoded string.

    Args:
        args (List[str]): Arguments passed to the `git` command.
        timeout (float): Maximum time in seconds to wait for the command.

    Returns:
        Optional[str]: Decoded output on success, or None on failure.
    """
    # Ensure git is available before trying
    if not _git_available():
        return None

    try:
        # Run git command with arguments, discard stderr
        out = subprocess.check_output(
            ["git", *args],
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )

        # Decode output to UTF-8 string
        return out.decode("utf-8", errors="ignore").strip()
    except Exception:
        # On failure, return None instead of raising
        return None


@lru_cache(maxsize=1)
def current_branch() -> Optional[str]:
    """Return the current Git branch name, or None if detached/unknown.

    Returns:
        Optional[str]: Branch name if available and not 'HEAD', else None.
    """
    # Ask git for the current branch name
    name = _run_git(["rev-parse", "--abbrev-ref", "HEAD"])

    # If branch name is missing or detached (HEAD), treat as None
    return None if not name or name == "HEAD" else name


@lru_cache(maxsize=1)
def list_local_branches() -> Optional[List[str]]:
    """List local Git branches as short names.

    Returns:
        Optional[List[str]]: List of local branch names, or None if unavailable.
    """
    # Ask git for all local branch references
    out = _run_git(["for-each-ref", "--format=%(refname:short)", "refs/heads"])
    if out is None:
        return None

    # Split output into lines and clean whitespace
    names = [ln.strip() for ln in out.splitlines() if ln.strip()]

    # Deterministic sorting could be applied if needed in future
    # names.sort()

    return names


def branch_index_1based(branch: Optional[str], branches: Optional[List[str]]) -> int:
    """Return the 1-based index of `branch` within `branches`.

    Args:
        branch (Optional[str]): Branch name to locate.
        branches (Optional[List[str]]): Ordered list of branch names.

    Returns:
        int: 1-based index if found; 0 otherwise.
    """
    # Validate inputs
    if not branch or not branches:
        return 0

    try:
        # Find zero-based index and convert to one-based
        return branches.index(branch) + 1
    except ValueError:
        # Return 0 if branch not found in list
        return 0


@lru_cache(maxsize=1)
def _base_branch() -> str:
    """Resolve the base branch used to compute the fork point.

    Returns:
        str: Base branch name, defaulting to 'main' if not overridden.
    """
    # Read from environment with fallback to "main"
    return os.getenv("FLY_BASE_BRANCH", "main")


@lru_cache(maxsize=1)
def _fork_point_with_base() -> Optional[str]:
    """Find the commit hash where the current branch diverged from base.

    It first attempts `merge-base --fork-point` and falls back to `merge-base`
    if the fork-point heuristic is unavailable.

    Returns:
        Optional[str]: Commit hash of the fork point, or None if not found.
    """
    # Identify which branch to compare against
    base = _base_branch()

    # First try: fork-point heuristic (best approximation)
    fp = _run_git(["merge-base", "--fork-point", base, "HEAD"])
    if fp:
        return fp

    # Fallback: common ancestor (less precise, but works everywhere)
    return _run_git(["merge-base", base, "HEAD"])


@lru_cache(maxsize=1)
def commit_count_from_branch_start() -> Optional[int]:
    """Count commits on HEAD since the branch diverged from its base.

    The count excludes commits that belong to the base branch history.

    Returns:
        Optional[int]: Number of commits since the fork point, or 0 if unknown.
    """
    # Locate fork point
    fork = _fork_point_with_base()
    if not fork:
        # Return 0 if no fork point found
        return 0

    # Count commits from fork point up to HEAD
    out = _run_git(["rev-list", "--count", f"{fork}..HEAD"])

    # Return numeric value only if output is a valid digit
    return int(out) if out and out.isdigit() else 0


def _resolve_state_override(override: Optional[int]) -> Optional[int]:
    """Resolve version state override from env or parameter.

    Env var `FLY_RELEASE_NUMBER` takes precedence over the function parameter.

    Args:
        override (Optional[int]): Optional state override provided by caller.

    Returns:
        Optional[int]: Final override value if present; otherwise None.
    """
    # Try environment override first
    env_num = os.getenv("FLY_RELEASE_NUMBER")

    # Convert env var to int if valid
    if env_num and env_num.isdigit():
        try:
            return int(env_num)
        except Exception:
            pass

    # Fallback to function argument
    return override


def _is_dev_env() -> bool:
    """Detect development/debug environment conditions.

    Considered "dev" if any of the following is true:
      - FLY_ENV is 'dev' or 'development'
      - FLY_DEBUG is 'true' or '1' (case-insensitive)
      - A debugger is attached (i.e., sys.gettrace() is not None)

    Returns:
        bool: True if running in a development/debug environment.
    """
    # Read environment flags
    env = os.getenv("FLY_ENV", "").lower()
    debug_flag = os.getenv("FLY_DEBUG", "").lower()

    # Detect attached debugger safely
    try:
        in_debugger = sys.gettrace() is not None
    except Exception:
        in_debugger = False

    # Dev environment if any of the conditions match
    return (
        env in {"dev", "development"}
        or debug_flag in {"1", "true", "yes"}
        or in_debugger
    )


@lru_cache(maxsize=1)
def current_commit_hash() -> Optional[str]:
    """Return the full 40-character commit hash for HEAD.

    Returns:
        Optional[str]: Commit hash if available, otherwise None.
    """
    # Ask git directly for HEAD hash
    return _run_git(["rev-parse", "HEAD"])


def compute_version(state_override: Optional[int] = None) -> str:
    """Compute a semantic-ish version string based on Git state.

    Format:
        'x.y.z {branch}/{commit}'

    Where:
        x: Environment state (0 in dev, 1 outside dev), or an explicit override
           provided by env var `FLY_RELEASE_NUMBER` or the function parameter.
        y: 1-based index of the current branch among local branches.
        z: Number of commits since the branch forked from the base branch.
        branch: Current branch name, or 'unknown' if not resolvable.
        commit: Full 40-character commit hash, or 'unknown' if not resolvable.

    Args:
        state_override (Optional[int]): Optional numeric override for `x`.

    Returns:
        str: Version string reflecting the current repository state.
    """
    # Step 1: resolve x (environment state)
    ov = _resolve_state_override(state_override)
    if ov is not None:
        x = ov
    else:
        x = 0 if _is_dev_env() else 1

    # Step 2: resolve y (branch index)
    br = current_branch()
    branches = list_local_branches()
    y = branch_index_1based(br, branches)

    # Step 3: resolve z (commits since fork point)
    z = commit_count_from_branch_start() or 0

    # Step 4: resolve display identifiers
    branch_name = br or "unknown"
    commit_hash = current_commit_hash() or "unknown"

    # Step 5: assemble final version string
    return f"{x}.{y}.{z} {branch_name}/{commit_hash}"


def get_version(
    fallback_release: str = "0.0.0", state_override: Optional[int] = None
) -> str:
    """Return the release string honoring explicit overrides and fallbacks.

    Precedence:
      1) If `FLY_RELEASE` is set, return its literal value (e.g., '1.4.12').
      2) Otherwise, compute a version via `compute_version(state_override)`.
      3) On any failure, return `fallback_release`.

    Args:
        fallback_release (str): Value returned if computation fails.
        state_override (Optional[int]): Optional numeric override for `x`.

    Returns:
        str: Final version string.
    """
    # Step 1: honor explicit release from env
    explicit = os.getenv("FLY_RELEASE")
    if explicit:
        return explicit

    # Step 2: try computing a dynamic version
    try:
        return compute_version(state_override)
    except Exception:
        # Step 3: fallback to safe default
        return fallback_release
