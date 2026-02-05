import ops
from ops import testing

from charm import TestObserverBackendCharm

def test_ingress_ready_sets_active_status():
    """Test that ingress ready event sets active status."""

    context = testing.Context(TestObserverBackendCharm)
    state_in = testing.State(
        relations={testing.Relation(endpoint="ingress")},
        containers={
            testing.Container(
                name="test-observer-api",
                can_connect=True,
            ),
        },
        leader=True,
    )
    state_out = context.run(context.ingress.on.ready, state_in)
