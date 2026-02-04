# Copyright (C) 2023 Canonical Ltd.
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
    from test_observer.common.metrics import test_executions_results

    test_executions_results.labels(**labels).inc()
"""

from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator, metrics

# Namespace for all metrics
NAMESPACE = "test_observer"

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

# Core metric - works for ALL families, always
test_results = Gauge(
    name=f"{NAMESPACE}_test_results",
    documentation="Test result counts by family, artefact, and test",
    labelnames=[
        "family",
        "artefact_name",
        "artefact_stage",
        "track",  # empty for deb/image
        "series",  # empty for snap/charm/image
        "os",  # empty for snap/charm/deb
        "environment_name",
        "test_plan",
        "test_name",
        "status",
    ],
)

# Triaged results with issue tracking
test_results_triaged = Gauge(
    name=f"{NAMESPACE}_test_results_triaged",
    documentation="Triaged test results with issue information",
    labelnames=[
        "family",
        "artefact_name",
        "artefact_stage",
        "track",
        "series",
        "os",
        "environment_name",
        "test_plan",
        "test_name",
        "status",
        "issue_source",
        "issue_project",
        "issue_key",
    ],
)

# Generic execution metadata metric
test_results_metadata = Gauge(
    name=f"{NAMESPACE}_test_results_metadata",
    documentation="Test results with arbitrary execution metadata",
    labelnames=[
        "family",
        "artefact_name",
        "artefact_stage",
        "track",  # empty for deb/image
        "series",  # empty for snap/charm/image
        "os",  # empty for snap/charm/deb
        "environment_name",
        "test_plan",
        "test_name",
        "status",
        "metadata_category",
        "metadata_value",
    ],
)
