"""
Centralized Logging Configuration.

Configures consistent standard library logging across all backend modules.
Ensures sensitive credentials, customer PII, and full datasets are never logged.
"""

import logging
import sys


def setup_logging(level: int = logging.INFO):
    """Initializes logging format, handler, and levels."""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Silence overly verbose third-party loggers
    logging.getLogger("cassandra").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
