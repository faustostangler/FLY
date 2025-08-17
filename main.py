print("Start!")
from infrastructure.config import ConfigAdapter
from infrastructure.logging import Logger

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
        pass

    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
    print('done!')
