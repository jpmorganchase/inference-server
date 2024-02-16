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
Functions for testing **inference-server** plugins
"""

import io
from types import ModuleType
from typing import Any, Callable, Optional, Protocol, Tuple, Type, Union

import botocore.response  # type: ignore[import-untyped]
import pluggy
import werkzeug.test

import inference_server
import inference_server._plugin


class ImplementsSerialize(Protocol):
    """Interface compatible with :class:`sagemaker.serializers.BaseSerializer`"""

    @property
    def CONTENT_TYPE(self) -> str:
        """The MIME type for the serialized data"""

    def serialize(self, data: Any) -> bytes:
        """Return the serialized data"""


class ImplementsDeserialize(Protocol):
    """Interface compatible with :class:`sagemaker.deserializers.BaseDeserializer`"""

    @property
    def ACCEPT(self) -> Tuple[str]:
        """The content types that are supported by this deserializer"""

    def deserialize(self, stream: botocore.response.StreamingBody, content_type: str) -> Any:
        """Return the deserialized data"""


class _PassThroughSerializer:
    """Serialize bytes as bytes"""

    @property
    def CONTENT_TYPE(self) -> str:
        """The MIME type for the serialized data"""
        return "application/octet-stream"

    def serialize(self, data: bytes) -> bytes:
        """Return the serialized data"""
        assert isinstance(data, bytes)
        return data


class _PassThroughDeserializer:
    """Deserialize bytes as bytes"""

    @property
    def ACCEPT(self) -> Tuple[str]:
        """The content types that are supported by this deserializer"""
        return ("application/octet-stream",)

    def deserialize(self, stream: "botocore.response.StreamingBody", content_type: str) -> Any:
        """Return the deserialized data"""
        assert content_type in self.ACCEPT
        try:
            return stream.read()
        finally:
            stream.close()


def predict(
    data: Any, serializer: Optional[ImplementsSerialize] = None, deserializer: Optional[ImplementsDeserialize] = None
) -> Any:
    """
    Invoke the model and return a prediction

    :param data:         Model input data
    :param serializer:   Optional. A serializer for sending the data as bytes to the model server. Should be compatible
                         with :class:`sagemaker.serializers.BaseSerializer`. Default: bytes pass-through.
    :param deserializer: Optional. A deserializer for processing the prediction as sent by the model server. Should be
                         compatible with :class:`sagemaker.deserializers.BaseDeserializer`. Default: bytes pass-through.
    """
    serializer = serializer or _PassThroughSerializer()
    deserializer = deserializer or _PassThroughDeserializer()

    serialized_data = serializer.serialize(data)
    http_headers = {
        "Content-Type": serializer.CONTENT_TYPE,  # The serializer declares the content-type of the input data
        "Accept": ", ".join(deserializer.ACCEPT),  # The deserializer dictates the content-type of the prediction
    }
    prediction_response = post_invocations(data=serialized_data, headers=http_headers)
    prediction_stream = botocore.response.StreamingBody(
        raw_stream=io.BytesIO(prediction_response.data),
        content_length=prediction_response.content_length,
    )
    prediction_deserialized = deserializer.deserialize(prediction_stream, content_type=prediction_response.content_type)
    return prediction_deserialized


def client() -> werkzeug.test.Client:
    """
    Return an HTTP test client for :mod:`inference_server`

    The test client is simply a :class:`werkzeug.test.Client` instance which loads the **inference-server** WSGI app.
    Consult the :mod:`werkzeug` documentation for details how to use the test client.
    """
    return werkzeug.test.Client(inference_server.create_app())


def post_invocations(**kwargs) -> werkzeug.test.TestResponse:
    """
    Send an HTTP POST request to ``/invocations`` using a test HTTP client and return the response

    This function should be used to verify an inference request using the full **inference-server** logic.

    :param kwargs: Keyword arguments passed to :meth:`werkzeug.test.Client.post`
    """
    response = client().post("/invocations", **kwargs)
    assert response.status_code == 200
    return response


def plugin_manager() -> pluggy.PluginManager:
    """Return the plugin manager used by **inference-server**"""
    return inference_server._plugin.manager()


def plugin_is_registered(plugin: Union[Type, ModuleType]) -> bool:
    """
    Return whether the given plugin is registered with :mod:`inference_server`

    This validates whether a plugin entrypoint is defined in :file:`pyproject.toml` like this:

    .. code-block:: toml

       [project.entry-points.inference_server]
       my_plugin_name = "my_module_name"

    :param plugin: The plugin, typically a module containg the hook functions.
    """
    return plugin_manager().is_registered(plugin)


def hookimpl_is_valid(function: Callable) -> bool:
    """
    Return whether the given function is a valid implementation of an :mod:`inference_server` hook

    :param function: The hook function to validate
    """
    try:
        hook = getattr(plugin_manager().hook, function.__name__)
    except AttributeError:
        return False
    return function in (impl.function for impl in hook.get_hookimpls())
