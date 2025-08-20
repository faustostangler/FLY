from __future__ import annotations

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
    try:
        # Load configuration
        config = ConfigAdapter()

        # Setup logger
        logger = Logger(config)

        # Log startup message
        logger.log(f"Run Project {config.fly_settings.app_name}", level="info")

        # Build controller
        controller = cli_factory(config, logger)

        # Run controller
        controller.run()

    except Exception as e:
        # Print unexpected error
        print(e)


if __name__ == "__main__":
    # Start application
    main()

    # Indicate finish
    print("done!")
