# infrastructure/config/version.py
from __future__ import annotations

import os
import shutil
import sys
import subprocess
from functools import lru_cache
from typing import Optional, List


def _git_available() -> bool:
    return shutil.which("git") is not None

def _run_git(args: List[str], timeout: float = 2.0) -> Optional[str]:
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


@lru_cache(maxsize=1)
def current_branch() -> Optional[str]:
    name = _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    return None if not name or name == "HEAD" else name

@lru_cache(maxsize=1)
def list_local_branches() -> Optional[List[str]]:
    out = _run_git(["for-each-ref", "--format=%(refname:short)", "refs/heads"])
    if out is None:
        return None
    names = [ln.strip() for ln in out.splitlines() if ln.strip()]
    # ordenação determinística para que o índice seja estável
    # names.sort()
    return names

def branch_index_1based(branch: Optional[str], branches: Optional[List[str]]) -> int:
    if not branch or not branches:
        return 0
    try:
        return branches.index(branch) + 1  # 1-based
    except ValueError:
        return 0

@lru_cache(maxsize=1)
def _base_branch() -> str:
    # branch base usada para calcular o ponto de criação; default 'main'
    return os.getenv("FLY_BASE_BRANCH", "main")

@lru_cache(maxsize=1)
def _fork_point_with_base() -> Optional[str]:
    base = _base_branch()
    # tenta o fork-point (melhor aproximação do "ponto em que a branch começou")
    fp = _run_git(["merge-base", "--fork-point", base, "HEAD"])
    if fp:
        return fp
    # fallback para merge-base simples, caso o fork-point não esteja disponível
    return _run_git(["merge-base", base, "HEAD"])

@lru_cache(maxsize=1)
def commit_count_from_branch_start() -> Optional[int]:
    """
    Conta os commits que existem em HEAD desde o ponto de criação da branch,
    sem contar os commits anteriores da base.
    """
    fork = _fork_point_with_base()
    if not fork:
        return 0  # não conseguiu detectar; opta por 0 para comportamento previsível
    out = _run_git(["rev-list", "--count", f"{fork}..HEAD"])
    return int(out) if out and out.isdigit() else 0


def _resolve_state_override(override: Optional[int]) -> Optional[int]:
    env_num = os.getenv("FLY_RELEASE_NUMBER")
    if env_num and env_num.isdigit():
        try:
            return int(env_num)
        except Exception:
            pass
    return override

def _is_dev_env() -> bool:
    """
    Detecta se está em ambiente de desenvolvimento/debug:
    - FLY_ENV=dev|development
    - FLY_DEBUG=true|1
    - Depurador ativo (sys.gettrace() não é None)
    """
    env = os.getenv("FLY_ENV", "").lower()
    debug_flag = os.getenv("FLY_DEBUG", "").lower()
    try:
        in_debugger = sys.gettrace() is not None
    except Exception:
        in_debugger = False

    return (
        env in {"dev", "development"}
        or debug_flag in {"1", "true", "yes"}
        or in_debugger
    )


def compute_version(state_override: Optional[int] = None) -> str:
    """
    Retorna 'x.y.z' onde:
      x = 0 se ambiente de desenvolvimento, 1 se não, ou N se injetado (override/env)
      y = índice 1-based da branch atual na lista de branches locais ordenada
      z = número de commits desde o início da branch (fork em relação à base)
    """
    # x (estado)
    ov = _resolve_state_override(state_override)
    if ov is not None:
        x = ov
    else:
        x = 0 if _is_dev_env() else 1

    # y (índice da branch)
    br = current_branch()
    branches = list_local_branches()
    y = branch_index_1based(br, branches)

    # z (commits desde o fork)
    z = commit_count_from_branch_start() or 0

    return f"{x}.{y}.{z}"

def get_version(fallback_release: str = "0.0.0",
                state_override: Optional[int] = None) -> str:
    """
    Prioridade:
      1) FLY_RELEASE: retorna o valor literal (ex.: '1.4.12')
      2) compute_version(state_override)
      3) fallback_release
    """
    explicit = os.getenv("FLY_RELEASE")
    if explicit:
        return explicit
    try:
        return compute_version(state_override)
    except Exception:
        return fallback_release
