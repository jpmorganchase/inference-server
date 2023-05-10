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

from types import ModuleType
from typing import Callable, Type, Union

import pluggy
import werkzeug.test

import inference_server
import inference_server._plugin


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
