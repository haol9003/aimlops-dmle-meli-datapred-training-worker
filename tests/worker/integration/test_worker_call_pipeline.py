from datetime import datetime, timedelta, timezone
from unittest import mock
from unittest.mock import ANY

import pytest
from cis.common.aml_conventions import AmlConventions
from cis.runtime.config import PipelineConfig
from dmle_meli_datapred_training_worker.worker.domain.worker import Worker


@pytest.fixture()
def request_json() -> dict:
    request = {
        "requestId": "12345",
        "application": "APP",
        "consumer": "CONSUMER",
        "country": "US",
        "client": "CLIENT",
        "characteristics": [
            "char",
        ],
        "input": {
            "assets": [
                {
                    "name": "test.csv",
                    "path": "dummy/path/to/test.cvs",
                }
            ]
        },
    }
    return request


@pytest.fixture()
def aml_workspace():
    return mock.Mock(name="ws", tags={"test": "true"})


@pytest.fixture()
def sas_token():
    return "mock_sas_token"


@pytest.fixture()
def cis_aml_conventions(request_json) -> AmlConventions:
    return AmlConventions(PipelineConfig.get_env(), request_json, "index", "any")



@pytest.fixture(scope="module")
def worker():
    return Worker(storage=mock.Mock())


@mock.patch("cis.runtime.infra.azure.auth.generate_container_sas")
@mock.patch("cis.runtime.infra.azure.auth.AccountSasPermissions")
@mock.patch("cis.runtime.infra.azure.azureml.PipelineEndpoint")
@mock.patch("cis.runtime.infra.azure.azureml.ServicePrincipalAuthentication")
@mock.patch("cis.runtime.infra.azure.azureml.Workspace")
def test_call_pipeline(
    ws_cls: mock.MagicMock,
    auth_cls: mock.MagicMock,
    endpoint_cls: mock.MagicMock,
    sas_permissions_cls: mock.MagicMock,
    generate_container_sas: mock.MagicMock,
    aml_workspace: mock.Mock,
    sas_token: mock.Mock,
    cis_aml_conventions: AmlConventions,
    request_json: dict,
    worker: Worker,
):
    """Tests the call_pipeline method."""
    ws_cls.return_value = aml_workspace
    generate_container_sas.return_value = sas_token

    # Expected values
    expected_service_principal_id = PipelineConfig.get_azureml_service_principal_id()
    expected_tenant_id = PipelineConfig.get_azureml_tenant_id()
    expected_subscription_id = PipelineConfig.get_azureml_subscription_id()
    expected_resource_group = PipelineConfig.get_azureml_resource_group()
    expected_workspace_name = PipelineConfig.get_azureml_workspace_name()
    expected_workspace_auth_secret = (
        PipelineConfig.get_azureml_service_principal_secret()
    )

    country = request_json["country"]
    request_id = request_json["requestId"]
    expected_pipeline_parameters = {
        "environment": PipelineConfig.get_env(),
        "country": country,
        "request_id": request_id,
    }

    worker.call_pipeline(request_json)

    auth_cls.assert_called_once_with(
        tenant_id=expected_tenant_id,
        service_principal_id=expected_service_principal_id,
        service_principal_password=expected_workspace_auth_secret,
    )

    ws_cls.assert_called_once_with(
        subscription_id=expected_subscription_id,
        resource_group=expected_resource_group,
        workspace_name=expected_workspace_name,
        auth=auth_cls.return_value,
    )

    sas_permissions_cls.assert_called_once_with(read=True, list=True, write=True)

    expected_pipeline_name = worker.cis_aml_conventions.pipeline_name
    endpoint_cls.get.assert_called_once_with(
        workspace=aml_workspace, name=expected_pipeline_name
    )

    endpoint_cls.get.return_value.submit.assert_called_once_with(
        experiment_name=cis_aml_conventions.experiment_name,
        pipeline_parameters=expected_pipeline_parameters,
    )

    pipeline_run = endpoint_cls.get.return_value.submit.return_value
    pipeline_run.set_tags.assert_called_once_with(cis_aml_conventions.get_cis_tags())
    pipeline_run.wait_for_completion.assert_called()


@mock.patch("cis.runtime.infra.azure.azureml.Workspace")
def test_auth_error(
    ws_cls: mock.MagicMock,
    worker: Worker,
    request_json: dict,
):
    """Tests that the auth exception is raised when calling the pipeline."""
    from azureml.exceptions import AuthenticationException

    ws_cls.side_effect = AuthenticationException("Auth error")
    with pytest.raises(AuthenticationException) as exc_info:
        worker.call_pipeline(request_json)
    assert "Auth error" in str(exc_info.value)
