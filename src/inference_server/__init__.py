# Copyright 2023 J.P. Morgan Chase & Co.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

"""
Pluggable Python HTTP web service (WSGI) for real-time AI/ML model inference compatible with Amazon SageMaker
"""

import enum
import functools
import http
import logging
from typing import TYPE_CHECKING

import codetiming
import orjson
import werkzeug
import werkzeug.exceptions
from werkzeug.datastructures import MIMEAccept

import inference_server._plugin
from inference_server._plugin import hook as plugin_hook

if TYPE_CHECKING:
    from _typeshed.wsgi import WSGIApplication

try:
    from importlib import metadata
except ImportError:  # pragma: no cover
    # Python < 3.8
    import importlib_metadata as metadata  # type: ignore

__all__ = (
    "BatchStrategy",
    "MIMEAccept",  # Exporting for plugin developers' convenience
    "create_app",
    "plugin_hook",
)

#: Library version, e.g. 1.0.0, taken from Git tags
__version__ = metadata.version("inference-server")

#: Well known location for model artifacts
_MODEL_DIR = "/opt/ml/model"

logger = logging.getLogger(__package__)


class BatchStrategy(enum.Enum):
    """
    Enumeration of Batch Transform invocation strategies

    Specifies the number of records to include in a mini-batch for an HTTP inference request. A record is a single unit
    of input data that inference can be made on. For example, a single line in a CSV file is a record.

    See: https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_CreateTransformJob.html#sagemaker-CreateTransformJob-request-BatchStrategy
    """  # noqa: E501

    #: Batch Transform job to invoke the model with a single record per request
    SINGLE_RECORD = "SingleRecord"
    #: Batch Transform job to invoke the model with multiple records per request
    MULTI_RECORD = "MultiRecord"


def create_app() -> "WSGIApplication":
    """Initialize and return the WSGI application"""
    return _app


def warmup() -> None:
    """Initialize any additional resources upfront"""
    _model()


@werkzeug.Request.application
def _app(request: werkzeug.Request) -> werkzeug.Response:
    """Return the WSGI application"""
    try:
        route_handler = _ROUTES[(request.method, request.path)]
    except KeyError:
        raise werkzeug.exceptions.NotFound()
    response = route_handler(request)
    return response


def _handle_invocations(request: werkzeug.Request) -> werkzeug.Response:
    """
    Handle an incoming inference POST request

    :param request: HTTP request data
    """
    with codetiming.Timer(text="Invocation took {:.3f} seconds", logger=logger.debug):
        pm = inference_server._plugin.manager()
        # Deserialize HTTP body payload (bytes) into input features
        data = pm.hook.input_fn(input_data=request.data, content_type=request.content_type)
        # Then use the model to make a prediction
        prediction = pm.hook.predict_fn(data=data, model=_model())
        # Then serialize the data as bytes. This is often (but not necessarily) JSON bytes.
        prediction_bytes, content_type = pm.hook.output_fn(prediction=prediction, accept=request.accept_mimetypes)
        return werkzeug.Response(prediction_bytes, mimetype=content_type)


def _handle_ping(request: werkzeug.Request) -> werkzeug.Response:
    """
    Handle an incoming ping HEAD request

    :param request: HTTP request data
    """
    pm = inference_server._plugin.manager()
    if pm.hook.ping_fn(model=_model()):
        status = http.HTTPStatus.OK
    else:
        status = http.HTTPStatus.SERVICE_UNAVAILABLE
    return werkzeug.Response(status=status)


def _handle_execution_parameters(request: werkzeug.Request):
    """
    Handle an incoming execution-parameters GET request

    This will enable BatchTransform job to choose the optimal tuning parameters during runtime.
    :param request: HTTP request data
    """
    pm = inference_server._plugin.manager()
    response_data = {
        "BatchStrategy": pm.hook.batch_strategy(),
        "MaxConcurrentTransforms": pm.hook.max_concurrent_transforms(),
        "MaxPayloadInMB": pm.hook.max_payload_in_mb(),
    }
    return werkzeug.Response(orjson.dumps(response_data), mimetype="application/json")


# Stupidly simple request routing
_ROUTES = {
    ("GET", "/execution-parameters"): _handle_execution_parameters,
    ("POST", "/invocations"): _handle_invocations,
    ("GET", "/ping"): _handle_ping,
}


@functools.lru_cache(maxsize=None)
def _model() -> inference_server._plugin.ModelType:
    """
    Load a previously serialized ML model from a given filesystem directory
    """
    pm = inference_server._plugin.manager()
    logger.info("Loading model using 'model_fn' hook...")
    model = pm.hook.model_fn(model_dir=_MODEL_DIR)
    logger.info("Finished loading model %s", model)
    return model
