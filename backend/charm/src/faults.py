class UnitReadinessFault:
    """A ReadinessFault describes the reason for a unit not to be ready."""

    def __init__(self, reason: str, parent: "UnitReadinessFault" | None = None):
        self.reason = reason

    def __str__(self):
        """Build a representation by recursively traversing the fault hierarchy in reverse order."""
        reversed_hierarchy = self.hierarchy().reverse()
        return "Not ready: " + " -> ".join([fault.reason for fault in reversed_hierarchy])

    def hierarchy(self):
        """Build a list of faults by recursively traversing the fault hierarchy."""
        if self.parent is None:
            return [self]
        else:
            return self.parent.hierarchy() + [self]
