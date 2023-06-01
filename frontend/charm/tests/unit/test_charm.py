# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest

import ops
import ops.testing
from charm import TestObserverFrontendCharm


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = ops.testing.Harness(TestObserverFrontendCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_pebble_ready(self):
        expected_plan = {
            "services": {
                "test-observer-frontend": {
                    "override": "replace",
                    "summary": "nginx",
                    "command": "nginx -g 'daemon off;'",
                    "startup": "enabled",
                }
            },
        }

        self.harness.container_pebble_ready("frontend")
        updated_plan = self.harness.get_container_pebble_plan(
            "frontend"
        ).to_dict()

        self.assertEqual(expected_plan, updated_plan)

        service = self.harness.model.unit.get_container(
            "frontend"
        ).get_service("test-observer-frontend")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, ops.ActiveStatus())

    def test_relating(self):
        harness = ops.testing.Harness(TestObserverFrontendCharm)
        harness.set_leader(True)
        self.addCleanup(harness.cleanup)

        rel_id = harness.add_relation("test-observer-rest-api", "backend")
        harness.container_pebble_ready("frontend")
        harness.set_can_connect("frontend", True)
        harness.update_config({"test-observer-api-scheme": "https://"})
        harness.update_config({"hostname": "teh-backend"})
        harness.update_config({"port": 443})
        harness.begin_with_initial_hooks()

        harness.add_relation_unit(rel_id, "backend/0")
        # harness.update_relation_data(
        #    rel_id, "backend", {"hostname": "teh-backend", "port": "443"}
        # )

        service = harness.model.unit.get_container("frontend").get_service(
            "test-observer-frontend"
        )
        self.assertTrue(service.is_running())
        self.assertEqual(harness.model.unit.status, ops.ActiveStatus())

        nginx_config = (
            harness.model.unit.get_container("frontend")
            .pull("/etc/nginx/conf.d/default.conf")
            .read()
        )
        print(nginx_config)

    def test_config_invalid_port(self):
        self.harness.set_can_connect("frontend", True)
        self.harness.update_config({"port": -1})
        self.assertIsInstance(
            self.harness.model.unit.status, ops.BlockedStatus
        )

    def test_config_invalid_api_scheme(self):
        self.harness.set_can_connect("frontend", True)
        self.harness.update_config({"test-observer-api-scheme": "foobar"})
        self.assertIsInstance(
            self.harness.model.unit.status, ops.BlockedStatus
        )

    def test_config_empty_hostname(self):
        self.harness.set_can_connect("frontend", True)
        self.harness.update_config({"hostname": ""})
        self.assertIsInstance(
            self.harness.model.unit.status, ops.BlockedStatus
        )
