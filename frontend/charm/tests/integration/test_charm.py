#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio
import logging
from pathlib import Path

import pytest
import yaml
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(Path("./metadata.yaml").read_text())
APP_NAME = METADATA["name"]


@pytest.mark.abort_on_fail
async def test_build_and_deploy_without_backend(ops_test: OpsTest):
    """Build the charm-under-test and deploy it together without related charms.

    Assert on the unit status before any relations/configurations take place.
    """
    charm = await ops_test.build_charm(".")
    resources = {"frontend-image": METADATA["resources"]["frontend-image"]["upstream-source"]}

    await asyncio.gather(
        ops_test.model.deploy(charm, resources=resources, application_name=APP_NAME),
        ops_test.model.wait_for_idle(
            apps=[APP_NAME],
            status="maintenance",
            timeout=2000,
        ),
    )
