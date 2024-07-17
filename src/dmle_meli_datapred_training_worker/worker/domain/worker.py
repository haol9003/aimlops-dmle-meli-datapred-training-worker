from cis.common.aml_conventions import AmlConventions
from cis.runtime.config import PipelineConfig
from cis.runtime.workers import PipelineWorker
from typing_extensions import override


class Worker(PipelineWorker):
    """A worker to invoke an AzureML pipeline.

    Only a few hooks (methods) have to be implemented to make this worker work.
    Feel free to override other methods in the parent class to customize the behavior.
    """

    @override
    def _build_cis_aml_conventions(self, request_json: dict) -> AmlConventions:
        """The conventions to be used to call the AzureML pipeline."""
        return AmlConventions(
            cis_env=PipelineConfig.get_env(),
            input_json=request_json,
            pipeline_country="any",
            pipeline_suffix="pipeline_test",
        )

    @override
    def _build_pipeline_display_name(self, request_json: dict) -> str:
        """The custom name of the pipeline to show in the AzureML WebUI."""

    @override
    def _build_pipeline_parameters(self, request_json: dict) -> dict:
        """The parameters to invoke the pipeline endpoint."""

