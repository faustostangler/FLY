from __future__ import annotations
import setup_env


from infrastructure.config.config_adapter import ConfigAdapter
from infrastructure.factories.cli_factory import cli_factory
from infrastructure.logging.logger_adapter import Logger


def main() -> None:
    """Run the FLY application.

    Steps:
        1. Load config
        2. Setup logger
        3. Build controller
        4. Run controller
    """
    # Load configuration
    config = ConfigAdapter()

    # Setup logger
    logger = Logger(config)

    # Log startup message
    logger.log(f"Run Project {config.fly_settings.app_name}", level="info")

    try:
        # Build controller
        controller = cli_factory(config, logger)

        # Run controller
        controller()

    except Exception as e:
        # Print unexpected error
        logger.log(f"Critical error: {e}")

if __name__ == "__main__":
    # Start application
    main()

    # Indicate finish
    print("done!")
