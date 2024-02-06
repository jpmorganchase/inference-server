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
Default plugin implementing simple data pass-through hooks
"""

from typing import Callable, Tuple

import werkzeug.datastructures

import inference_server

ModelType = Callable[[bytes], bytes]


@inference_server.plugin_hook(trylast=True)
def model_fn(model_dir: str) -> ModelType:
    """
    Load a previously serialized ML model from a given filesystem directory

    :param model_dir: Local filesystem directory containing model files
    """
    return lambda data: data


@inference_server.plugin_hook(trylast=True)
def ping_fn(model: ModelType) -> bool:
    """
    Return whether the model is OK up and running

    :param model: Model object
    """
    return True


@inference_server.plugin_hook(trylast=True)
def input_fn(input_data: bytes, content_type: str) -> bytes:
    """
    Deserialize data sent over HTTP

    The input_fn function is responsible for deserializing your input data so that it can be passed to your model. It
    takes input data and content type as parameters, and returns deserialized data.

    :param input_data:   Raw HTTP body data
    :param content_type: MIME type, e.g. ``application/json``
    """
    return input_data


@inference_server.plugin_hook(trylast=True)
def predict_fn(data: bytes, model: ModelType) -> bytes:
    """
    Apply inference to input features and return a prediction

    The predict_fn function is responsible for getting predictions from the model. It takes the model and the data
    returned from input_fn as parameters, and returns the prediction.

    :param data:  Deserialized input features
    :param model: Model object
    """
    return model(data)


@inference_server.plugin_hook(trylast=True)
def output_fn(prediction: bytes, accept: werkzeug.datastructures.MIMEAccept) -> Tuple[bytes, str]:
    """
    Serialize the prediction as bytes to be sent over HTTP, return tuple of (content, content_type)

    The output_fn function is responsible for serializing the data that the predict_fn function returns as a prediction.

    :param prediction: The output from the model
    :param accept:     MIME types requested/accepted by the client, e.g. ``application/json``
    """
    return prediction, "application/octet-stream"


@inference_server.plugin_hook(trylast=True)
def batch_strategy() -> inference_server.BatchStrategy:
    """
    Return Batch Transform processing strategy.
    """
    return inference_server.BatchStrategy.MULTI_RECORD


@inference_server.plugin_hook(trylast=True)
def max_concurrent_transforms() -> int:
    """
    Return maximum number of parallel requests.
    """
    return 1


@inference_server.plugin_hook(trylast=True)
def max_payload_in_mb() -> int:
    """
    Return the maximum allowed size in MB of the payload.
    """
    return 6
