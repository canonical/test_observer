from ops.charm import CharmBase
from ops.main import main

class FastAPIDemoCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)

if __name__ == "__main__":  # pragma: nocover
    main(FastAPIDemoCharm)