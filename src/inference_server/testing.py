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
Public functions for testing plugins
"""

from types import ModuleType
from typing import Callable, Type, Union

import pluggy
import werkzeug.test

import inference_server
import inference_server._plugin


def client() -> werkzeug.test.Client:
    """Return an HTTP test client for :mod:`inference_server`"""
    return werkzeug.test.Client(inference_server.create_app())


def post_invocations(**kwargs) -> werkzeug.test.TestResponse:
    """Send an HTTP POST request to ``/invocations`` using a test HTTP client"""
    response = client().post("/invocations", **kwargs)
    assert response.status_code == 200
    return response


def plugin_manager() -> pluggy.PluginManager:
    """Return the plugin manager"""
    return inference_server._plugin.manager()


def plugin_is_registered(plugin: Union[Type, ModuleType]) -> bool:
    """Return whether the given plugin is registered with :mod:`inference_server`"""
    return plugin_manager().is_registered(plugin)


def hookimpl_is_valid(function: Callable) -> bool:
    """Return whether the given function is a valid implementation of a :mod:`inference_server` hook"""
    try:
        hook = getattr(plugin_manager().hook, function.__name__)
    except AttributeError:
        return False
    return function in (impl.function for impl in hook.get_hookimpls())
