Introduction
============

**inference-server** is a Python library to deploy an AI/ML model to Amazon SageMaker for real-time inference. The
library simplifies deploying a model using your own Docker container image.


Basic steps to deploy a model
-----------------------------

#. Define a Docker container image containing the model and all dependencies.
#. Write a couple of **inference-server** *hooks* as simple Python functions defining how the model should be loaded and
   invoked. Details: :ref:`hooks:Implementing server hooks`.
#. Install a Python :abbr:`WSGI (Web Server Gateway Interface)` web server of your choice into the Docker image and
   configure it to start the **inference-server** application. Details: :ref:`deployment:Deployment`.
#. Build the container image and deploy the image to a registry such as Amazon :abbr:`ECR (Elastic Container Registry)`.
#. Deploy the Amazon SageMaker real-time inference endpoint using the AWS Console or a preferred CI/CD pipeline.


Comparison with Amazon's SageMaker Inference Toolkit
----------------------------------------------------

Amazon's "SageMaker Inference Toolkit" (https://github.com/aws/sagemaker-inference-toolkit) is an alternative library to
serve Machine Learning models with SageMaker.

The following table compares **inference-server** with SageMaker Inference Toolkit.

=================  =================================================  =================================================
Aspect             **inference-server**                               SageMaker Inference Toolkit
=================  =================================================  =================================================
Model integration  Defined through 4 plain Python functions. Input /  Defined through an "InferenceHandler" class with
                   output functions can be packaged independently.    4 methods plus a "HandlerService" class plus a
                   Details: :ref:`hooks:Implementing server hooks`.   Python entrypoint script.

Web server         Any Python WSGI server. Documentation for          Java web server (using Amazon Multi Model
                   recommended Gunicorn provided. Details:            Server).
                   :ref:`deployment:Deployment`.

Testing            Testing functions included to test model           Not available.
                   integration functions and webserver invocation.
                   Details: :ref:`testing:Testing`.
=================  =================================================  =================================================
