"""Pytest configuration file.

Please, add here all the fixtures that you want to use in your tests.
"""
import shutil
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def tmp_dir(tmp_path_factory: pytest.TempPathFactory) -> Generator[Path]:
    """Like tmp_path but with module scope to use on test cases with module scope."""
    path = tmp_path_factory.mktemp("pytest")
    yield path
    shutil.rmtree(str(path), ignore_errors=True)

