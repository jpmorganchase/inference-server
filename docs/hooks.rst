.. currentmodule:: inference_server._plugin

Implementing server hooks
=========================

This page explains how to implement the **inference-server** hooks to deploy a model to Amazon SageMaker.


Hook definitions
----------------

**inference-server** defines 4 hooks that can be implemented to deploy a model as a SageMaker Docker container:

.. autofunction:: model_fn
.. autofunction:: input_fn
.. autofunction:: predict_fn
.. autofunction:: output_fn

.. note::

   These hooks follow an API very similar to the Amazon SageMaker Inference Toolkit. See
   https://docs.aws.amazon.com/sagemaker/latest/dg/adapt-inference-container.html

A 5th hook is available to implement custom health-checks if required:

.. autofunction:: ping_fn


Implementing model hooks
-------------------------

To implement the server hooks for a model, we need to create a Python package. In this example, we will be deploying a
shipping (weather) forecast model.

We will setup the following files::

   shipping_forecast/
   ├── pyproject.toml
   ├── src/
   │   └── shipping_forecast/
   │       └── __init__.py
   └── tests/

Then we define the server hook functions inside :file:`__init__.py`.

First of all, the actual model::

   import inference_server

   DataType = str
   PredictionType = Dict[str, str]
   ModelType = Callable[[DataType], PredictionType]

   @inference_server.plugin_hook
   def model_fn(model_dir: str) -> ModelType:
       """Return a function that returns the weather forecast for a given location at sea"""
       return _predict_weather

   def _predict_weather(location: DataType) -> PredictionType:
       """It's stormy everywhere"""
       return {
           "wind": "Southwesterly gale force 8 continuing",
           "sea_state": "Rough or very rough, occasionally moderate in southeast.",
           "weather": "Thundery showers.",
           "visibility": "Good, occasionally poor.",
       }

(Type hint imports have been omitted for brevity.)

To make predictions, we implement the following function::

   @inference_server.plugin_hook
   def predict_fn(data: DataType, model: ModelType) -> PredictionType:
       """Invoke a prediction for given input data"""
       return model(data)

The above implementation is a common pattern: **inference-server** ships with a *default* implementation for
this hook which does exactly that. If we are happy with that default implementation, there is no need to define our own
:func:`predict_fn`!


Implementing deserialization/serialization hooks
------------------------------------------------

To integrate the model with the HTTP server, we need to wire up the deserialization and serialization functions.

To deserialize the input data, let's assume the following JSON payload should be sent for a single invocation:

.. code-block:: json

   {"location": "Fair Isle"}

With the shipping forecast model that would require the following :func:`input_fn`::

   import orjson

   @inference_server.plugin_hook
   def input_fn(input_data: bytes, content_type: Literal["application/json"]) -> DataType:
       """Deserialize JSON bytes and return ``location`` attribute"""
       return orjson.loads(input_data)["location"]

Bear in mind that this a fairly naive implementation of course as it does not apply any input validation on the payload
or the content type. Here we use a fast JSON serializer :mod:`orjson` which natively serializes to and from bytes
instead of string objects.

In this example, the predictions should be returned using the following JSON structure:

.. code-block:: json

   {
       "wind": "Southwesterly gale force 8 continuing",
       "sea_state": "Rough or very rough, occasionally moderate in southeast.",
       "weather": "Thundery showers.",
       "visibility": "Good, occasionally poor."
   }

That requires a simple :func:`output_fn` like this::

   @inference_server.plugin_hook
   def output_fn(prediction: PredictionType, accept: inference_server.MIMEAccept) -> Tuple[bytes, str]:
       """Serialize predictions as JSON"""
       assert accept.accept_json
       return orjson.dumps(prediction), "application/json"

This function validates that a JSON serialization is acceptable to the application invoking the prediction. However,
error handling should be improved here.

.. tip::

   The 4 plugin hooks may be implemented and installed using different Python modules or packages. For example, this
   could be used to develop a package with JSON serialization/deserialization hooks which could be shared between many
   different model packages. In that case, the model packages would need to define the :func:`model_fn` and
   :func:`predict_fn` hooks only.


Registering the hooks
---------------------

To register the hooks with **inference-server**, we need to add some metadata to the :mod:`shipping_forecast`
package. In this example, we use :mod:`setuptools` with **entry point** metadata defined in :file:`pyproject.toml`.
Other *build backends* may support entry point definitions too.

.. seealso::

   Setuptools entry point documentation
      https://setuptools.pypa.io/en/latest/userguide/entry_point.html#entry-points-for-plugins

Add the following content to :file:`pyproject.toml`:

.. code-block:: toml

   [project.entry-points.inference_server]
   shipping_forecast = "shipping_forecast"

This configuration states that we are a supplying an entry point under the group ``inference_server``. The entry
point is named ``shipping_forecast`` and it refers to the *package* :mod:`shipping_forecast` since we defined the
server hooks in :file:`shipping_forecast/__init__.py`.

.. note::

   Additional package metadata should be recorded as with any other Python package. See https://setuptools.pypa.io/ for
   further details.
