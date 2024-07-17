"""This package contains the code to listen requests in CIS from consumers.

The worker will be responsible to run the code in the CIS environment. It will receive the
request from the consumer and will dispatch the request to the correct pipeline(s)
(PipelineWorker) or just run the inference code to get the predictions (InferenceWorker).
"""
