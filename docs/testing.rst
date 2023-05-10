Testing
=======

This page explains how to test implemented **inference-server** hooks using the example from
:ref:`hooks:Implementing server hooks`.


Verifying plugin registration
-----------------------------

To verify out model is registered correctly as a plugin, we use this::

   from inference_server import testing
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


Testing model predictions
-------------------------

To the test a complete model invocation, we use this::

   def test_prediction_is_ok():
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
