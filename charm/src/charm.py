from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus
from ops.pebble import Layer
import logging

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)


class TestObserverCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.pebble_service_name = "test-observer"
        self.framework.observe(self.on.api_pebble_ready, self._on_api_pebble_ready)


def _pebble_layer(self) -> Layer:
    return Layer(
        {
            "summary": "test observer",
            "description": "pebble config layer for Test Observer",
            "services": {
                self.pebble_service_name: {
                    "override": "replace",
                    "summary": "test observer",
                    "command": " ".join(
                        ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port=30000"]
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
