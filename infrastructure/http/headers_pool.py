# infrastructure/http/headers_pool.py
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict

from infrastructure.config.scraping import load_scraping_config


@dataclass(frozen=True)
class HeadersPool:
    user_agents: list[str]
    referers: list[str]
    languages: list[str]

    @classmethod
    def from_config(cls) -> "HeadersPool":
        cfg = load_scraping_config()
        return cls(cfg.user_agents, cfg.referers, cfg.languages)

    def sample(self) -> Dict[str, str]:
        # sorteia uma combinação coerente a cada sessão/tentativa
        return {
            "User-Agent": random.choice(self.user_agents),
            "Referer": random.choice(self.referers),
            "Accept-Language": random.choice(self.languages),
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }
