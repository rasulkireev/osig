import structlog


def get_osig_logger(name):
    """This will add a `osig` prefix to logger for easy configuration."""

    return structlog.get_logger(f"osig.{name}")
