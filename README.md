# inference-server

Deploy your AI/ML model to Amazon SageMaker for Real-Time Inference and Batch Transform using your own Docker container image.

:blue_book: Documentation: https://inference-server.readthedocs.io


## Installing

```shell
python -m pip install inference-server
```

## Developing

To setup a scratch/development virtual environment (under `.venv/`), first install [Tox][].
Then run:

```shell
tox -e dev
```

The `inference-server` package is installed in [editable mode][] inside the `.venv/` environment.

Run tests by simply calling `tox`.

Install code quality Git hooks using `pre-commit install --install-hooks`.


## Terms & Conditions

Copyright 2023 J.P. Morgan Chase & Co.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.


## Contributing

See [CONTRIBUTING.md][]


[Tox]:                  https://tox.wiki
[editable mode]:        https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-e
[CONTRIBUTING.md]:      https://github.com/jpmorganchase/.github/blob/main/CONTRIBUTING.md
