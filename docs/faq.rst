Frequently Asked Questions (FAQ)
================================


Is my "model_fn" called at each invocation?
-------------------------------------------

No.

The :func:`model_fn` function is called during the very fist invocation only.
Once the model has been loaded, it is retained in memory for as long as the service runs.

To speed up the very first invocation, it is possible to trigger the `model_fn` hook in advance.
To do this, simply call :func:`inference_server.warmup`.

For example, when using Gunicorn, this could be done from a post-fork Gunicorn hook::

   def post_fork(server, worker):
       worker.log.info("Warming up worker...")
       inference_server.warmup()


Does **inference-server** support async/ASGI webservers?
--------------------------------------------------------

No.

**inference-server** is a WSGI application to be used by synchronous webservers.

For most ML models that will be the correct choice as model inference is typically CPU-bound.
Therefore, a multi-process based WSGI server is a good choice whereby the number of workers is equal to the number of CPU cores available.

For more details see :ref:`deployment:Configuring Gunicorn workers`.


My model is leaking memory, how do I address that?
--------------------------------------------------


How do I invoke my model using a data stream from my favourite message queue system?
------------------------------------------------------------------------------------
