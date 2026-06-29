<!--
Copyright 2026 Canonical Ltd.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
SPDX-License-Identifier: Apache-2.0
-->

# Contributing

## Dependencies

The Python project is managed with [uv](https://docs.astral.sh/uv/), and testing is managed with [Task](https://taskfile.dev/). Charms are built with [charmcraft](https://documentation.ubuntu.com/charmcraft/latest/).

```shell
snap install astral-uv --classic
snap install task --classic
snap install charmcraft --classic
```

To fully deploy the charm, you'll need a working
[development setup](https://documentation.ubuntu.com/juju/3.6/howto/manage-your-deployment/#set-up-your-deployment-local-testing-and-development).


## Build the charm

Build the charm using:

```shell
charmcraft pack
```

## Format, Lint, and and Run Unit Tests

To easily standardize the code and run unit tests, use `task`:

```shell
# Run the format, lint, and unit-test tasks by default...
task

# ...or run them each individually
task format
task lint
task unit-test
```

Since integration tests are heavier, they are not run by default.
The integration tests also require the charm to be built first.

```shell
# run `charmcraft pack` first
task integration-test
```
