class ByteFormatter:
    """Utility class to present byte counts in a human-readable format."""

    def format_bytes(self, bytes_amount: int) -> str:
        """Convert a raw byte count into a formatted string.

        Chooses the largest suitable binary unit (B, KB, MB, GB) and
        returns a string representation with two decimal places.

        Args:
            bytes_amount (int): The number of bytes to format.

        Returns:
            str: A human-readable string representing the byte size.
        """

        # Use bytes if less than 1 KB
        if bytes_amount < 1024:
            return f"{bytes_amount:.2f}B"

        # Use kilobytes if less than 1 MB
        elif bytes_amount < 1024**2:
            return f"{bytes_amount / 1024:.2f}KB"

        # Use megabytes if less than 1 GB
        elif bytes_amount < 1024**3:
            return f"{bytes_amount / (1024**2):.2f}MB"

        # Use gigabytes otherwise
        else:
            return f"{bytes_amount / (1024**3):.2f}GB"
