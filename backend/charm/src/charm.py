#!/usr/bin/env python3

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import Layer
from requests import get
import logging

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)


class TestObserverCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.pebble_service_name = "test-observer"

        logger.info("Containers")
        logger.info(self.unit.containers)
        self.container = self.unit.get_container("api")
        self.framework.observe(self.on.api_pebble_ready, self._on_api_pebble_ready)
        self.framework.observe(self.on.config_changed, self._update_layer_and_restart)

    def _on_config_changed(self, event):
        self.unit.status = MaintenanceStatus("Reconfiguring")
        self._update_layer_and_restart(None)
        self.unit.status = ActiveStatus()

    def _update_layer_and_restart(self, event):
        self.unit.status = MaintenanceStatus(
            f"Updating {self.pebble_service_name} layer"
        )

        if self.container.can_connect():
            self.container.add_layer(
                self.pebble_service_name, self._pebble_layer, combine=True
            )
            self.container.restart(self.pebble_service_name)
            self.unit.set_workload_version(self.version)
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("Waiting for Pebble for API")

    @property
    def version(self) -> str | None:
        if self.container.can_connect() and self.container.get_services(
            self.pebble_service_name
        ):
            try:
                return get(f"http://localhost:{self.config['port']}/version").json()[
                    "version"
                ]
            except Exception as e:
                logger.warning(f"Failed to get version: {e}")
                logger.exception(e)
        return None

    @property
    def _pebble_layer(self) -> Layer:
        return Layer(
            {
                "summary": "test observer",
                "description": "pebble config layer for Test Observer",
                "services": {
                    self.pebble_service_name: {
                        "override": "replace",
                        "summary": "test observer API server",
                        "command": " ".join(
                            [
                                "uvicorn",
                                "src.main:app",
                                "--host",
                                "0.0.0.0",
                                f"--port={self.config['port']}",
                            ]
                        ),
                        "startup": "enabled",
                    }
                },
            }
        )

    def _on_api_pebble_ready(self, event):
        container = event.workload
        container.add_layer("test-observer", self._pebble_layer, combine=True)
        container.replan()
        self.unit.status = ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    main(TestObserverCharm)
