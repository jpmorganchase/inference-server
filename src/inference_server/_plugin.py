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
Plugin logic

Hook definitions adapted from https://docs.aws.amazon.com/sagemaker/latest/dg/adapt-inference-container.html
"""

import functools
import logging
import sys
from typing import TYPE_CHECKING, Any, Tuple

import pluggy
import werkzeug.datastructures

if TYPE_CHECKING:
    import inference_server

ModelType = Any
DataType = Any
PredictionType = Any

logger = logging.getLogger(__package__)

#: Decorator for plugin hook functions
hook = pluggy.HookimplMarker(__package__)
#: Decorator for plugin hook function specifications/signatures
hookspec = pluggy.HookspecMarker(__package__)


@hookspec(firstresult=True)
def model_fn(model_dir: str) -> ModelType:
    """
    A function which loads a model in memory from a given filesystem directory.

    This function will be called when the server starts up. Here, ``ModelType`` can be any Python class corresponding to
    the model, for example :class:`sklearn.tree.DecisionTreeClassifier`.

    :param model_dir: Local filesystem directory containing the model files
    """
    raise NotImplementedError


@hookspec(firstresult=True)
def ping_fn(model: ModelType) -> bool:
    """
    A functions wich indicates whether the web application is up and running.

    In most cases, there is no need to implement this function as the default implementation simply returns ``True``.
    Such an implementation simply confirms that the model is initialized correctly using the :func:`model_fn` and that
    the webserver (e.g. Gunicorn) is able to respond to HTTP requests.

    For more advanced scenarios, any logic could be implemented provided it's reasonably fast.

    :param model: Model object
    """
    raise NotImplementedError


@hookspec(firstresult=True)
def input_fn(input_data: bytes, content_type: str) -> DataType:
    """
    A function which converts data sent over an HTTP connection to the input data format the model is expecting.

    Typically, the HTTP transport uses JSON bytes, but in theory, this could be any serialization format.

    The :func:`input_fn` is called as the first hook for each inference invocation/request.

    :param input_data:   Raw HTTP body data
    :param content_type: The content type (MIME) corresponding with the body data, e.g. ``application/json``
    """
    raise NotImplementedError


@hookspec(firstresult=True)
def predict_fn(data: DataType, model: ModelType) -> PredictionType:
    """
    A function which invokes the model and returns a prediction.

    Argument ``data`` will be populated with the output from :func:`input_fn` and ``model`` will be the output from
    :func:`model_fn`. Data types should therefore correspond between these functions.

    Apply inference to input features and return a prediction

    The predict_fn function is responsible for getting predictions from the model. It takes the model and the data
    returned from input_fn as parameters, and returns the prediction.

    :param data:  Deserialized input features (the output from :func:`input_fn`)
    :param model: Model object (the output from :func:`model_fn`)
    """
    raise NotImplementedError


@hookspec(firstresult=True)
def output_fn(prediction: PredictionType, accept: werkzeug.datastructures.MIMEAccept) -> Tuple[bytes, str]:
    """
    A function which seriazizes and returns the prediction as bytes along with the corresponding MIME type.

    The returned data would typically be JSON bytes (MIME type ``aplication/json``), but in theory this could be any
    serialization format as long as the application which invokes the prediction *accepts* this type. The
    :func:`output_fn` implementation should therefore compare the ``accept`` argument value with the implemented
    serialization format(s).

    :param prediction: The output from the model as return by :func:`predict_fn`
    :param accept:     MIME type(s) requested/accepted by the client, e.g. ``application/json``
    """
    raise NotImplementedError


@hookspec(firstresult=True)
def batch_strategy() -> "inference_server.BatchStrategy":
    """
    Return the default Batch Transform invocation strategy for this model

    Default: :attr:`inference_server.BatchStrategy.MULTI_RECORD`

    If users do not specify a strategy when creating a Batch Transform job, the strategy returned by this hook will be
    used.

    A model may support one or multiple invocation strategies depending on its implementation of the server hooks.
    """
    raise NotImplementedError


@hookspec(firstresult=True)
def max_concurrent_transforms() -> int:
    """
    Return the optimal maximum number of concurrent invocations for this model

    Default: ``1``

    If users do not specify a maximum number of concurrent transforms when creating a Batch Transform job, the value
    returned by this hook will be used.
    """
    raise NotImplementedError


@hookspec(firstresult=True)
def max_payload_in_mb() -> int:
    """
    Return the maximum allowed size in MB of a single record submitted by a Batch Transform job to the model

    Default: ``6`` (MB)

    The value of :func:`max_payload_in_mb` × :func:`max_concurrent_transforms` should be ≤ 100 MB.
    """
    raise NotImplementedError


@functools.lru_cache(maxsize=None)
def manager() -> pluggy.PluginManager:
    """
    Return a manager to discover and load plugins for providing hooks

    Plugins are automatically loaded through (setuptools) entrypoints, group ``inference_server``.
    """
    from inference_server import default_plugin

    logger.debug("Initializing plugin manager for '%s'", __package__)
    manager_ = pluggy.PluginManager(__package__)
    manager_.add_hookspecs(sys.modules[__name__])

    logger.debug("Loading default plugin '%s'", default_plugin.__name__)
    manager_.register(default_plugin)
    logger.debug("Discovering plugins using entrypoint group '%s'", __package__)
    manager_.load_setuptools_entrypoints(group=__package__)
    logger.debug("Loaded plugins: %s", manager_.get_plugins())
    return manager_
