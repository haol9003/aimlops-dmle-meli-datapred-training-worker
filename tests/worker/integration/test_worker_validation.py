from collections.abc import Generator
from unittest import mock

import pytest
from dmle_meli_datapred_training_worker.worker.domain.worker import Worker
from dmle_common_redis_utils.redis_caching import Caching
from wrapper_worker.core.redis_utils import RedisUtils


@pytest.fixture()
def request_json():
    return {
        "requestId": "12345",
        "application": "APP",
        "consumer": "CONSUMER",
        "country": "US",
        "client": "CLIENT",
        "characteristics": ["char"],
        "input": {
            "assets": [
                {
                    "name": "test.csv",
                    "path": "dummy/path/to/test.csv",
                    "delimiter": "comma",
                }
            ]
        },
    }


@pytest.fixture()
def redis_metadata(request_json: dict) -> Generator[Caching]:
    cache = RedisUtils.get_redis_metadata()
    app = request_json["application"]
    consumer = request_json["consumer"]
    country = request_json["country"]
    chars = request_json["characteristics"][0]
    prefix = f"{app}_{consumer}_{country}_{chars}".lower()
    for suffix in ("model", "service", "property"):
        cache.set_value(key=f"{prefix}_{suffix}", value='{"key": "value"}')
    yield cache
    cache.flush_all()


def get_storage(found: bool) -> mock.Mock:
    return mock.Mock(
        check_file=mock.Mock(side_effect=None if found else Exception("Not found"))
    )


def test_worker_validate_request(request_json: dict, redis_metadata: Caching):
    """Tests that the request validation is performed correctly."""
    assert redis_metadata.get_matched_keys("*") is not None

    worker = Worker(storage=get_storage(True))
    result, message = worker.validate_request(request_json, None)
    assert result is True
    assert message is not None

    result, message = worker.validate_request({}, None)
    assert result is False
    assert message is not None

    worker = Worker(storage=get_storage(False))
    ok, msg = worker.validate_request(request_json, None)
    assert not ok
    assert msg.startswith("Input files not found")


@pytest.mark.parametrize("asset_path", [" ", "  ", "", ".", '""'])
def test_worker_validate_request_bad_files(request_json, asset_path, redis_metadata):
    request_json["input"]["assets"] = [
        {
            "name": "test.csv",
            "path": asset_path,
        }
    ]
    worker = Worker(storage=get_storage(True))
    ok, msg = worker.validate_request(request_json, None)
    assert not ok
