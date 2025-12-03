"""Command-line entry point for the FLY application."""

from infrastructure.config import Config
from infrastructure.factories import create_datacleaner
from infrastructure.logging import Logger
from presentation import CLIAdapter


def main() -> None:
    """Initialize and run the FLY application via the command-line interface.

    This function executes the following startup sequence:
    - Instantiates the configuration object (``Config``).
    - Creates the main logger.
    - Creates the data cleaner component.
    - Instantiates the CLI controller with injected dependencies.
    - Starts the application logic by calling ``controller.start_fly()``.
    """
    # Inicializa a configuração
    config = Config()
    logger = Logger(config)

    try:
        # Load CLI
        logger.log(
            "Run Project FLY",
            level="info",
        )

        # Load datacleaner
        datacleaner = create_datacleaner(config, logger)

        # Entry point for the FLY CLI application.
        # logger.log("Instantiate controller", level="info")
        controller = CLIAdapter(config=config, logger=logger, datacleaner=datacleaner)

        # Run Controller
        # logger.log("Call Method controller.start()", level="info")
        controller.start_fly()
        # logger.log("End  Method controller.start()", level="info")

        # logger.log("End Instance controller", level="info")

        # Finaliza a execução com uma mensagem de confirmação
        logger.log(
            "Finish Project FLY",
            level="info",
        )
    except Exception as e:  # pragma: no cover
        logger.log(f"Erro {e}", level="info", show_path=True)


if __name__ == "__main__":
    main()
