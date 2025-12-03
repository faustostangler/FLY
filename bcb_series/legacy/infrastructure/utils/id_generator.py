# infrastructure/utils/id_generator.py
from __future__ import annotations

import hashlib
import os
import platform
import socket
import time
import uuid
from typing import Optional

from domain.ports import ConfigPort


class IdGenerator:
    """Responsável por criar identificadores curtos, únicos e legíveis para
    threads ou processos de trabalho.

    • prefixo: nome da aplicação em maiúsculas (p.ex. “FLY”) • ts_part:
    timestamp em milissegundos, codificado em hexadecimal • rand_part: 8
    hex pseudo-aleatórios do UUID-4
    """

    def __init__(self, config: ConfigPort, logger_name: str = "FLY") -> None:
        self.config = config
        self.logger_name = logger_name or self.config.global_settings.app_name or "FLY"

    def create_id(self, size: int = 0, string_id: Optional[str] = None) -> str:
        """Retorna um novo identificador no formato PREFIX-timestamp-random."""
        if string_id:
            base = string_id.encode("utf-8")
        else:
            salt = self.logger_name
            system = platform.system()
            release = platform.release()
            version = platform.version()
            machine = platform.machine()
            processor = platform.processor()
            mac = f"{uuid.getnode():012x}"
            hostname = socket.gethostname()
            fqdn = socket.getfqdn()
            node = platform.node()
            user = os.environ.get("USER") or os.environ.get("USERNAME")
            home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
            ts = time.time_ns()
            rand = uuid.uuid4().hex

            composite_str = f"{salt}-{system}-{release}-{version}-{machine}-{processor}-{mac}-{hostname}-{fqdn}-{node}-{user}-{home}-{ts}-{rand}"

            base = composite_str.encode("utf-8")

        digest = hashlib.sha256(base).hexdigest()
        # digest = hashlib.sha512(full_id).hexdigest()

        return digest[:size] if size else digest
