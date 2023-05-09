Introduction
============

**inference-server** is a Python library to deploy an AI/ML model to Amazon SageMaker for real-time inference.

Basic steps to deploy a model:

#. Define a Docker container image containing the model and all dependencies.
#. Write a couple of **inference-server** *hooks* as simple Python functions defining how the model should be loaded and
   invoked. Details: :ref:`hooks:Implementing server hooks`.
#. Install a Python :abbr:`WSGI (Web Server Gateway Interface)` web server of your choice into the Docker image and configure it to start the
   **inference-server** application. Details: :ref:`deployment:Deployment`.
#. Build the container image and deploy the image to a registry such as Amazon :abbr:`ECR (Elastic Container Registry)`.
#. Deploy the Amazon SageMaker real-time inference endpoint using the AWS Console or a preferred CI/CD pipeline.
