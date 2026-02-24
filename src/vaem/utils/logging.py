"""Logger for VAEM device."""

import logging

from rich.logging import RichHandler


class Logging:
    """Class that contains common functions for logging."""

    logger = logging.getLogger("vaem")

    def __init__(self, logging_level=logging.INFO, filename=None) -> None:
        """
        Constructor for logging class.

        Args:
            logging_level (int): Logging level from logging module
            filename (str): If provided, enables file logging to the given filename.

        Returns:
            None
        """
        logging.basicConfig(format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])

        Logging.logger.setLevel(logging_level)
        Logging.logger.propagate = False

        if filename:
            self.enable_file_logging(logging_level, filename)
        else:
            self.enable_stream_logging(logging_level)

    def enable_stream_logging(self, logging_level=logging.INFO) -> None:
        """
        Enables logging to stream using the provided log level with rich log formatting.

        Args:
            logging_level (int): Logging level from logging module

        Returns:
            None
        """
        handler = RichHandler()
        handler.setLevel(logging_level)
        formatter = logging.Formatter(fmt="%(message)s", datefmt="[%X]")
        handler.setFormatter(formatter)
        Logging.logger.addHandler(handler)

    def enable_file_logging(self, logging_level=logging.INFO, filename=None) -> None:
        """
        Enables logging to a file using the provided filename and log level.

        Args:
            logging_level (int): Logging level from logging module
            filename (str): Filename to log to.

        Returns:
            None
        """
        handler = logging.FileHandler(filename)
        handler.setLevel(logging_level)
        formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="[%X]")
        handler.setFormatter(formatter)
        Logging.logger.addHandler(handler)
