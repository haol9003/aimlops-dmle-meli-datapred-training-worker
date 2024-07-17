import json
from collections.abc import Generator
from unittest import mock

import pytest
from azureml.pipeline.core import PipelineEndpoint
from cis.runtime.messages.pipeline_message import PipelineMessage
from dmle_meli_datapred_training_worker.worker.domain.worker import Worker
from dmle_common_redis_utils.redis_caching import Caching
from wrapper_worker.core.redis_utils import RedisUtils

@pytest.fixture()
def expected_pipeline_name():
    """The name of the pipeline endpoint to call."""
    return "rnd_app_any_pipeline"


@pytest.fixture()
def request_json() -> dict:
    """A request received from the consumer."""
    return {
        "requestId": "12345",
        "application": "app",
        "consumer": "any",
        "characteristics": [""],
        "country": "US",
        "client": "OGRDS",
    }


@pytest.fixture()
def expected_redis_key(request_json: dict):
    x = request_json
    return f"{x['application']}_{x['consumer']}_{x['characteristics'][0]}_{x['requestId']}_{x['country']}".lower()


@pytest.fixture()
def redis_cache(expected_redis_key: str) -> Generator[Caching]:
    """Sets up the Redis cache with the expected key before execution."""
    cache = RedisUtils.get_redis_caching()
    cache.set_value(
        key=expected_redis_key,
        value=json.dumps({"input": {}}),
    )
    yield cache
    cache.flush_all()


def test_e2e_pipeline(
    request_json: dict, redis_cache: Caching, expected_pipeline_name: str
):
    """Tests that the pipeline can be run through the worker without waiting."""
    assert len(redis_cache.get_all()) == 1
    pipeline_run = mock.Mock()
    pipeline_run.wait_for_completion.side_effect = lambda show_output: print(
        "Pipeline test is completed but the real pipeline was not launched."
    )
    worker = Worker(storage=mock.Mock())
    with (
        mock.patch.object(PipelineEndpoint, "submit", return_value=pipeline_run),
        mock.patch(
            "cis.common.aml_conventions.AmlConventions.pipeline_name",
            new_callable=mock.PropertyMock,
        ) as mock_pipeline_name,
    ):
        mock_pipeline_name.return_value = expected_pipeline_name
        status, msg = worker.ml_exec_request(request_json, None, None)
    assert status
    assert msg == PipelineMessage.pipeline_completed
    pipeline_run.set_tags.assert_called_once()
    pipeline_run.wait_for_completion.assert_called_once()
