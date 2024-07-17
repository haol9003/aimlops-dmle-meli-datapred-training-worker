"""Pytest configuration file.

Add here all the fixtures that you want available in all your e2e tests.
"""

import logging
import os
from pathlib import Path
from unittest import mock

import pytest
import yaml

RESOURCE_PATH = Path(__file__).parent / "resources"

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def _inject_config(tmp_path: Path):
    """Adapts the environment to use the resources in this folder for E2E tests."""
    from wrapper_worker.config import Config

    path = RESOURCE_PATH / "worker_config" / "config.yaml"
    e2e_config = yaml.safe_load(path.read_text())
    e2e_config["unittest"]["dmle_output_home_path"] = str(tmp_path)
    logger.info(f"Injecting E2E config: {e2e_config}")
    with mock.patch.object(Config, "config", e2e_config):
        yield

