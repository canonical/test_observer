# Copyright (C) 2026 Canonical Ltd.
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


from test_observer.data_access.models import TestExecution


def extract_endpoint_info(
    test_plan: str, target_asset: str
) -> tuple[str, str, str, str]:
    """
    Extract provider_endpoint, interface, requirer_endpoint, and neighbor_asset
    from test_plan.

    The test_plan format is:
    integration/$PROVIDER_ENDPOINT/$INTERFACE/$REQUIRER_ENDPOINT

    Args:
        test_plan: Test plan string from test execution
        target_asset: The target asset name to identify which is the neighbor

    Returns:
        Tuple of (provider_endpoint, interface, requirer_endpoint, neighbor_asset)
        Returns empty strings if parsing fails
    """
    parts = test_plan.split("/")
    if len(parts) < 4:
        return "", "", "", ""

    provider_endpoint = parts[1] if len(parts) > 1 else ""
    interface = parts[2] if len(parts) > 2 else ""
    requirer_endpoint = parts[3] if len(parts) > 3 else ""

    if not provider_endpoint or not interface or not requirer_endpoint:
        return "", "", "", ""

    # Extract assets from both endpoints (format: ASSET:ENDPOINT)
    provider_asset = (
        provider_endpoint.split(":", 1)[0] if ":" in provider_endpoint else ""
    )
    requirer_asset = (
        requirer_endpoint.split(":", 1)[0] if ":" in requirer_endpoint else ""
    )

    # Determine neighbor asset (the one that's not the target)
    assets = [provider_asset, requirer_asset]
    if target_asset in assets:
        assets.remove(target_asset)

    neighbor_asset = assets[0] if assets else ""

    return provider_endpoint, interface, requirer_endpoint, neighbor_asset


def get_common_metric_labels(test_execution: TestExecution) -> dict[str, str]:
    """
    Extract common metric labels from a test execution.

    Returns a dict with the common labels used across multiple metrics:
    - target_asset, target_track, target_risk
    - provider_endpoint, interface, requirer_endpoint, neighbor_asset
    """
    artefact = test_execution.artefact_build.artefact
    test_plan_name = test_execution.test_plan.name
    target_asset = artefact.name

    # Extract endpoint info from test plan
    provider_endpoint, interface, requirer_endpoint, neighbor_asset = (
        extract_endpoint_info(test_plan_name, target_asset)
    )

    return {
        "target_asset": artefact.name,
        "target_track": artefact.track or "",
        "target_risk": artefact.stage,
        "provider_endpoint": provider_endpoint,
        "interface": interface,
        "requirer_endpoint": requirer_endpoint,
        "neighbor_asset": neighbor_asset,
    }
