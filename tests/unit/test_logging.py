import logging

from app.logging.logger import configure_logging, get_logger


def test_configure_logging_sets_level_and_single_handler() -> None:
    configure_logging("WARNING")

    root = logging.getLogger()
    assert root.level == logging.WARNING
    assert len(root.handlers) == 1


def test_configure_logging_is_idempotent() -> None:
    configure_logging("INFO")
    configure_logging("INFO")

    assert len(logging.getLogger().handlers) == 1


def test_get_logger_returns_named_logger() -> None:
    logger = get_logger("synapse.test")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "synapse.test"
