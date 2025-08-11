# infrastructure/config/version.py
from __future__ import annotations

import os
import sys
import shutil
import subprocess
from functools import lru_cache
from typing import Optional


# ---------- util git ----------

def _git_available() -> bool:
    return shutil.which("git") is not None

def _run_git(args: list[str], timeout: float = 2.0) -> Optional[str]:
    if not _git_available():
        return None
    try:
        out = subprocess.check_output(
            ["git", *args],
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
        return out.decode("utf-8", errors="ignore").strip()
    except Exception:
        return None


# ---------- detecção de ambiente ----------

def _is_dev() -> bool:
    env = os.getenv("FLY_ENV", "").lower()
    debug_flag = os.getenv("FLY_DEBUG", "").lower()
    return (
        env in {"dev", "development"}
        or debug_flag in {"1", "true", "yes"}
        or bool(sys.gettrace())
    )

@lru_cache(maxsize=1)
def current_branch() -> Optional[str]:
    name = _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    return None if not name or name == "HEAD" else name


# ---------- métricas de repo ----------

@lru_cache(maxsize=1)
def branch_count_local() -> Optional[int]:
    out = _run_git(["for-each-ref", "--format=%(refname:short)", "refs/heads"])
    if out is None:
        return None
    return len([ln for ln in out.splitlines() if ln.strip()])

@lru_cache(maxsize=8)
def commit_count_since(base_ref: str, head: str = "HEAD") -> Optional[int]:
    """
    Conta commits alcançáveis em HEAD que **não** estão no base_ref (ex.: main..HEAD).
    """
    out = _run_git(["rev-list", "--count", f"{base_ref}..{head}"])
    return int(out) if out and out.isdigit() else None

@lru_cache(maxsize=4)
def _base_branch() -> str:
    # permite configurar a base via ambiente; default "main"
    return os.getenv("FLY_BASE_BRANCH", "main")


# ---------- versão ----------

def compute_dev_version(prefix: str = "0.30",
                        include_branch_name: bool = False) -> Optional[str]:
    """
    Versão dinâmica em dev:
      {prefix}.{commits_desde_base}-b{branches}[-{branch}]
    Ex.: 0.30.12-b7 ou 0.30.12-b7-feature-x
    """
    if not _is_dev():
        return None

    base = _base_branch()
    cc = commit_count_since(base_ref=base)
    if cc is None:
        return None

    bc = branch_count_local()
    suffix_b = f"-b{bc}" if bc is not None else ""

    name = current_branch() if include_branch_name else None
    suffix_name = f"-{name}" if name else ""

    return f"{prefix}.{cc}{suffix_b}{suffix_name}"

def get_version(fallback_release: str = "0.30.524",
                prefix_for_dev: str = "0.30") -> str:
    """
    Prioridade:
      1) FLY_RELEASE (definida no ambiente em CI/CD)
      2) compute_dev_version(prefix_for_dev)  [usa commits desde a base]
      3) fallback_release fixo
    """
    return (
        os.getenv("FLY_RELEASE")
        or compute_dev_version(prefix_for_dev)
        or fallback_release
    )


# ---------- (opcional) exportar métricas para logs/CLI ----------

def get_branch_count_local() -> Optional[int]:
    return branch_count_local()

def get_commit_count_since_base() -> Optional[int]:
    return commit_count_since(_base_branch())
