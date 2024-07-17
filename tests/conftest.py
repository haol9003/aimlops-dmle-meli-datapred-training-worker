"""Pytest configuration file.

Please, add here all the fixtures that you want to use in your tests.
"""
import os
import shutil
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.worker.conftest import RESOURCE_PATH

@pytest.fixture(scope="module")
def tmp_dir(tmp_path_factory: pytest.TempPathFactory) -> Generator[Path]:
    """Like tmp_path but with module scope to use on test cases with module scope."""
    path = tmp_path_factory.mktemp("pytest")
    yield path
    shutil.rmtree(str(path), ignore_errors=True)

def pytest_sessionstart(session):
    """Set the CONFIG_PATH variable to a default to avoid exceptions."""
    # FIXME: this can be removed once we refactor the old wrapper_worker library
    os.environ["CONFIG_PATH"] = str(RESOURCE_PATH / "config")


def pytest_sessionfinish(session):
    os.environ.pop("CONFIG_PATH", None)


@pytest.fixture(autouse=True)
def mock_log_path(tmp_path):
    with patch("wrapper_worker.config.Config.get_log_file_path") as mock_log_path:
        mock_log_path.return_value = tmp_path
        yield mock_log_path
