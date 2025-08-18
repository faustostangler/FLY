from __future__ import annotations

from infrastructure.config.config import ConfigAdapter
from infrastructure.factories import cli_factory
from infrastructure.logging import Logger
from presentation.controllers import Cli

# Uso na Application
# from domain.ports.logger_port import LoggerPort
# from infrastructure.logging.std_logger_adapter import StdLoggerAdapter
# logger: LoggerPort = StdLoggerAdapter()
# facade = LoggerFacade(logger)
# facade.info("Starting ParseStatementsProcessor")


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
