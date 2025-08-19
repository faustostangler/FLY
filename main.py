from __future__ import annotations

from infrastructure.config.config_adapter import ConfigAdapter
from infrastructure.factories.cli_factory import cli_factory
from infrastructure.logging.logger_adapter import Logger


def main() -> None:
    try:
        config = ConfigAdapter()
        logger = Logger(config)

        logger.log(
            f"Run Project {config.fly_settings.app_name}",
            level="info",
        )

        controller = cli_factory(config, logger)

        controller.run()

    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
    print('done!')
