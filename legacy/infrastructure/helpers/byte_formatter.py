class ByteFormatter:
    """Utility to present byte counts in a human readable format."""

    def format_bytes(self, bytes_amount: int) -> str:
        """Return a formatted string for ``bytes_amount`` using binary units."""

        # Determine the appropriate unit based on the byte count
        if bytes_amount < 1024:
            return f"{bytes_amount:.2f}B"
        elif bytes_amount < 1024**2:
            return f"{bytes_amount / 1024:.2f}KB"
        elif bytes_amount < 1024**3:
            return f"{bytes_amount / (1024**2):.2f}MB"
        else:
            return f"{bytes_amount / (1024**3):.2f}GB"
