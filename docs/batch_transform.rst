.. currentmodule:: inference_server._plugin

Batch Transform
===============

**inference-server** supports both SageMaker Real-Time Inference and Batch Transform.

The following additional plugin hooks may be implemented to define Batch Transform **execution parameters**. One or
multiple hooks may be implemented as required.

.. autofunction:: batch_strategy
.. autofunction:: max_concurrent_transforms
.. autofunction:: max_payload_in_mb


.. seealso::

   SageMaker Inference Options
      https://docs.aws.amazon.com/sagemaker/latest/dg/deploy-model.html#deploy-model-options

   SageMaker Batch Transform execution parameters
      https://docs.aws.amazon.com/sagemaker/latest/dg/your-algorithms-batch-code.html#your-algorithms-batch-code-how-containe-serves-requests
