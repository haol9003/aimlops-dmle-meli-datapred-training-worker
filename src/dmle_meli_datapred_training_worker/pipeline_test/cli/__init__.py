"""This package contains the CLI to parse the arguments to run the commands.

We recommend the use of jsonargparse library to parse the arguments and config.
"""

from .cli import MainCLI, main

__all__ = ["MainCLI", "main"]
