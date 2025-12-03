from __future__ import annotations

import hashlib
import os
import platform
import socket
import time
import uuid
from typing import Optional

from application.ports.config_port import ConfigPort


class IdGenerator:
    """Create short, unique, human-readable identifiers for worker threads/processes.

    The identifier is derived from either an explicit `string_id` or a composite
    string built from environment and runtime attributes, then hashed for
    uniformity and privacy.

    Format (conceptual):
        PREFIX-timestamp-random

    Notes:
        - "PREFIX" comes from the application name (e.g., "FLY") and is taken
          from `logger_name` or `config.fly_settings.app_name`.
        - The resulting string is *not* a raw concatenation; it is a SHA-256
          hex digest of the chosen base string, optionally truncated.

    Attributes:
        config (ConfigPort): Configuration provider used to read app identity.
        logger_name (str): Fallback/app name used as a salt when composing the base.
    """

    def __init__(self, config: ConfigPort, logger_name: str = "FLY") -> None:
        """Initialize the generator with configuration and optional app name.

        Args:
            config (ConfigPort): Configuration port exposing `fly_settings`.
            logger_name (str): Preferred application name to use as salt.
                Falls back to `config.fly_settings.app_name` and then "FLY".
        """
        # Keep a reference to the configuration port
        self.config = config

        # Resolve the effective logger/app name with sensible fallbacks
        self.logger_name = logger_name or self.config.fly_settings.app_name or "FLY"

    def create_id(self, size: int = 0, string_id: Optional[str] = None, random: bool = True) -> str:
        """Return a new identifier as a hex digest (optionally truncated).

        If `string_id` is provided, it becomes the sole basis for the hash.
        Otherwise, a composite string using system/user/runtime attributes is
        constructed and hashed to produce a stable-length identifier.

        Args:
            size (int): Optional max number of hex characters to return.
                If 0 or falsy, the full digest is returned.
            string_id (Optional[str]): Optional explicit base string to hash.

        Returns:
            str: Hex-encoded identifier (SHA-256), truncated to `size` if given.
        """
        # Use the provided base string if available
        if string_id:
            base = string_id.encode("utf-8")
        else:
            # Collect a stable salt from app identity
            salt = self.logger_name

            # Capture OS and hardware identifiers to diversify the base
            system = platform.system()
            release = platform.release()
            version = platform.version()
            machine = platform.machine()
            processor = platform.processor()

            # Use MAC address for additional entropy (formatted as 12 hex chars)
            mac = f"{uuid.getnode():012x}"

            # Gather network/host identifiers
            hostname = socket.gethostname()
            # fqdn = socket.getfqdn()
            fqdn = ''
            node = platform.node()

            # Add user-specific context from environment, when present
            user = os.environ.get("USER") or os.environ.get("USERNAME")
            home = os.environ.get("HOME") or os.environ.get("USERPROFILE")

            if random:
                # Include a high-resolution timestamp for temporal uniqueness
                ts = time.time_ns()

                # Add a random UUID4 component for extra entropy
                rand = uuid.uuid4().hex
            else:
                ts = ''
                rand = ''

            # Build the composite string deterministically from all pieces
            composite_str = f"{salt}-{system}-{release}-{version}-{machine}-{processor}-{mac}-{hostname}-{fqdn}-{node}-{user}-{home}-{ts}-{rand}"

            # Encode the composite string as bytes for hashing
            base = composite_str.encode("utf-8")

        # Compute a SHA-256 digest for uniform, fixed-length output
        digest = hashlib.sha256(base).hexdigest()

        # Note: SHA-512 would increase length and cost with little practical benefit here.
        # The line below is intentionally left commented as an alternative.
        # digest = hashlib.sha512(full_id).hexdigest()

        # Return a truncated digest when `size` is specified; otherwise the full digest
        return digest[:size] if size else digest
