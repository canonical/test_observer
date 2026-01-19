# Copyright (C) 2025 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Prometheus metrics for Test Observer.

This module provides a centralized location for all Prometheus metrics.
Metrics can be imported and updated from anywhere in the codebase.

Example usage:
    from test_observer.common.metrics import test_executions_started_total

    test_executions_started_total.labels(family="snap", environment="laptop").inc()
"""

from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator, metrics

# Namespace for all metrics
NAMESPACE = "t_obs"

# Create instrumentator instance with configuration
# This will be used in main.py to instrument the FastAPI app
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=False,
    should_respect_env_var=False,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

# Add default metrics (HTTP requests, duration, size)
instrumentator.add(
    metrics.default(
        metric_namespace=NAMESPACE,
        metric_subsystem="api",
    )
)

# Custom metrics for Test Observer domain
# These can be imported and updated from any module

test_executions_results = Gauge(
    name=f"{NAMESPACE}_results",
    documentation="Test result counts from Test Observer API",
    labelnames=[
        "target_asset",
        "target_track",
        "target_risk",
        "provider_endpoint",
        "interface",
        "requirer_endpoint",
        "neighbor_asset",
        "test_name",
        "status",
    ],
)

test_executions_results_triaged = Gauge(
    name=f"{NAMESPACE}_results_triaged",
    documentation="Triaged test result counts from Test Observer API",
    labelnames=[
        "target_asset",
        "target_track",
        "target_risk",
        "provider_endpoint",
        "interface",
        "requirer_endpoint",
        "neighbor_asset",
        "test_name",
        "status",
        "issue_source",
        "issue_project",
        "issue_key",
        "issue_url",
    ],
)

test_execution_results_metadata_charm_revision = Gauge(
    name=f"{NAMESPACE}_results_metadata_charm_revision",
    documentation="Charm revision metadata from test executions",
    labelnames=[
        "target_asset",
        "target_track",
        "target_risk",
        "provider_endpoint",
        "interface",
        "requirer_endpoint",
        "neighbor_asset",
        "test_name",
        "status",
        "charm_name",
        "charm_revision",
    ],
)

test_execution_results_metadata_charm_failure = Gauge(
    name=f"{NAMESPACE}_results_metadata_charm_failure",
    documentation="Charm revision metadata from test executions",
    labelnames=[
        "target_asset",
        "target_track",
        "target_risk",
        "provider_endpoint",
        "interface",
        "requirer_endpoint",
        "neighbor_asset",
        "test_name",
        "status",
        "charm_name",
        "entity_type",
        "charm_status",
        "status_message",
    ],
)

test_executions_results_metadata_charm_cli = Gauge(
    name=f"{NAMESPACE}_results_metadata_failure_cli",
    documentation="CLI command and stderr metadata from test failures",
    labelnames=[
        "target_asset",
        "target_track",
        "target_risk",
        "provider_endpoint",
        "interface",
        "requirer_endpoint",
        "neighbor_asset",
        "test_name",
        "status",
        "cmd",
        "stderr",
    ],
)

test_executions_results_metadata_simple = Gauge(
    name=f"{NAMESPACE}_results_metadata_simple",
    documentation="Simple key-value metadata from test executions",
    labelnames=[
        "target_asset",
        "target_track",
        "target_risk",
        "provider_endpoint",
        "interface",
        "requirer_endpoint",
        "neighbor_asset",
        "test_name",
        "status",
        "metadata_key",
        "metadata_value",
    ],
)
