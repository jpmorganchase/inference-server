Deployment
==========

This page explains how to deploy a model to Amazon SageMaker using **inference-server** using the example from
:ref:`hooks:Implementing server hooks`.


Docker container image
----------------------

SageMaker models are deployed using Docker container images. To create a docker image, we might use a :file:`Dockerfile`
like this:

.. code-block:: docker

   FROM python:3.10

   COPY entrypoint.sh /usr/local/bin/
   RUN python -m pip install \
       gunicorn  \
       shipping-forecast  # Our package implementing the hooks

   EXPOSE 8080
   ENTRYPOINT ["sh", "entrypoint.sh"]

The :file:`entrypoint.sh` script contains the following command only:

.. code-block:: sh

   python -m gunicorn --bind=0.0.0.0:8080 'inference_server:create_app()'

Here, ``gunicorn`` is the web server which handles incoming HTTP request and executes the **inference-server**
WSGI application. The package ``shipping-forecast`` implements the server hooks (in other words: our business logic),
see the example :ref:`hooks:Hook definitions`.

.. note::

   Unfortunately, we cannot add our Python command directly in the Dockerfile under ``ENTRYPOINT``. This is because AWS
   SageMaker starts the Docker container with an extra ``serve`` argument like this:

   .. code-block:: console

      docker run {image} serve

   The entrypoint script simply ignores this extra argument.


Configuring Gunicorn HTTP server
--------------------------------

For a typical deployment, we may need to configure additional Gunicorn options. Instead of adding command line options
one by one, we could simply specify all options in a single configuration file.

Create :file:`conf.py` with the following content::

   accesslog = "-"
   bind = "0.0.0.0:8080"
   logconfig = "/opt/gunicorn/logging.ini"
   loglevel = "DEBUG"
   workers = 2
   wsgi_app = "inference_server:create_app()"

And :file:`logging.ini` like this:

.. code-block:: ini

   [loggers]
   keys = root

   [handlers]
   keys = std_out

   [formatters]
   keys = default

   [logger_root]
   level = DEBUG
   handlers = std_out

   [handler_std_out]
   class = StreamHandler
   formatter = default
   args = (sys.stdout,)

   [formatter_default]
   format = %(asctime)s %(levelname)s %(message)s
   datefmt =
   class = logging.Formatter

Then we *replace* the content in :file:`entrypoint.sh` with this:

.. code-block:: sh

   python -m gunicorn --config=/opt/gunicorn/conf.py

Finally, we need to copy the configuration files into the container image in the :file:`Dockerfile`:

.. code-block:: docker

   COPY conf.py logging.ini /opt/gunicorn/

.. seealso::

   Configuration Overview
      https://docs.gunicorn.org/en/latest/configure.html
   :mod:`logging.config` — Logging configuration
      https://docs.python.org/3/library/logging.config.html
   Use Your Own Inference Code with Hosting Services
      https://docs.aws.amazon.com/sagemaker/latest/dg/your-algorithms-inference-code.html


Configuring Gunicorn workers
----------------------------

Typically, ML model predictions are CPU-bound logic and Gunicorn's default synchronous, multi-processing workers are a
good choice.

The optimal **number** of workers should be established emperically. It depends both on the model algorithm and the AWS
EC2 compute instance type. It is recommended to choose a *compute optimized* instance type as these types are designed
and priced for sustained high CPU utilization. Using a 4 vCPU instance, for example, the hypervisor would allocate 4
concurrent processor threads to our application. In theory, such an instance could achieve a CPU utilization of 400% as
shown in AWS CloudWatch Metrics.

A good starting point for the number of Gunicorn workers is to set this equal to the vCPU count, 4 in the above example.
To finetune the number of workers, we deploy a SageMaker model endpoint with a single EC2 instance, then send a large
batch of model invocation requests. CloudWatch Metrics should then be evaluated to identity the maximum CPU utilization.
A value well below 400% suggest there may be some I/O overhead and the number of Gunicorn workers may be increased to
achieve greater concurrency and CPU utilization.

.. seealso::

   Choosing a Worker Type
      https://docs.gunicorn.org/en/latest/design.html#choosing-a-worker-type
   Automatically Scale Amazon SageMaker Models
      https://docs.aws.amazon.com/sagemaker/latest/dg/endpoint-auto-scaling.html
