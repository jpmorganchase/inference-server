Testing
=======

This page explains how to test implemented **inference-server** hooks using the example from
:ref:`hooks:Implementing server hooks`.


Testing model predictions (high-level API)
------------------------------------------

To verify whether we have defined and registered all services hooks correctly, we use the
:mod:`inference_server.testing` module.

A full example looks like this::

   import sagemaker.deserializers
   import sagemaker.serializers

   from inference_server import testing

   def test_prediction_is_ok():
        input_data = {"location": "Fair Isle"}
        expected_prediction = {
            "wind": "Southwesterly gale force 8 continuing",
            "sea_state": "Rough or very rough, occasionally moderate in southeast.",
            "weather": "Thundery showers.",
            "visibility": "Good, occasionally poor."
        }

        prediction = testing.predict(
            input_data,
            serializer=sagemaker.serializers.JSONSerializer(),
            deserializer=sagemaker.deserializers.JSONDeserializer(),
        )
        assert prediction == expected_prediction

Here we can use any serializer compatible with :mod:`sagemaker.serializers` and any deserializer compatible with
:mod:`sagemaker.deserializers` from the AWS SageMaker SDK.

If no serializer or deserializer is configured, bytes data are passed through as is for both input and output.


Testing model predictions (low-level API)
-----------------------------------------

Instead of using the high-level testing API, we can also use invoke requests similar to the :mod:`requests` library::

   def test_prediction_request_is_ok():
       input_data = {"location": "Fair Isle"}
       expected_prediction = {
           "wind": "Southwesterly gale force 8 continuing",
           "sea_state": "Rough or very rough, occasionally moderate in southeast.",
           "weather": "Thundery showers.",
           "visibility": "Good, occasionally poor."
       }

       response = testing.post_invocations(
           json=input_data,
           content_type="application/json",
           headers={"Accept": "application/json"},
       )
       assert response.content_type == "application/json"
       assert response.json() == expected_prediction



Verifying plugin registration
-----------------------------

To verify the model is registered correctly as a plugin, we use this::

   import shipping_forecast

   def test_plugin_is_registered():
       assert testing.plugin_is_registered(shipping_forecast)

This simply verifies that we have declared the module as a plugin in :file:`pyproject.toml` like this:

.. code-block:: toml

   [project.entry-points.inference_server]
   shipping_forecast = "shipping_forecast"

If the test fails, but the above snippet is included in :file:`pyproject.toml` we possibly have not installed the model
package in our Python environment. It is recommend to use `Tox`_ for testing an *installed* package.

.. _Tox: https://tox.wiki


Verifying individual hook functions
-----------------------------------

To verify our function hooks have been defined correctly, we use this::

   def test_model_fn_hook_is_valid():
       assert testing.hookimpl_is_valid(shipping_forecast.model_fn)

   def test_predict_fn_hook_is_valid():
       assert testing.hookimpl_is_valid(shipping_forecast.predict_fn)
