from __future__ import annotations

from infrastructure.config.config_adapter import ConfigAdapter
from infrastructure.logging import Logger
from infrastructure.utils import datacleaner_factory

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
        datacleaner = datacleaner_factory(config, logger)
        datacleaner.
        logger.log(
            f"Run Project {config.fly_settings.app_name}",
            level="info",
        )
        pass

    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
    print('done!')
