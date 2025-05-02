import logging


def setup_logging():
    """Configures basic logging for the application."""
    logging.basicConfig(
        level=logging.INFO,  # Change to DEBUG for more verbose output
        format="%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Example: Quieten overly verbose libraries if needed
    # logging.getLogger("PIL").setLevel(logging.WARNING)
    # logging.getLogger("urllib3").setLevel(logging.WARNING)


# You can add other utility functions here if needed.
