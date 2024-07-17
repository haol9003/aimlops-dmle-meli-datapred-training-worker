"""Pytest configuration file.

Add here all the fixtures that you want available in all your worker tests.
"""

import logging
import os
from pathlib import Path
from unittest import mock

import pytest
import yaml

logger = logging.getLogger(__name__)

RESOURCE_PATH = Path(__file__).parent / "integration" / "resources"


@pytest.fixture(autouse=True)
def _inject_config(tmp_path: Path):
    """Injects the configuration to use on all worker tests by default."""
    from wrapper_worker.config import Config

    path = RESOURCE_PATH / "config" / "config.yaml"
    config = yaml.safe_load(path.read_text())
    config["unittest"]["dmle_output_home_path"] = str(tmp_path)
    logger.info(f"Injecting config: {config}")
    with mock.patch.object(Config, "config", config):
        yield


