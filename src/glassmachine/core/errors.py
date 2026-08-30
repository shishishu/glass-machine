"""Domain-specific failures that should never be silently ignored."""


class GlassMachineError(Exception):
    """Base class for expected GlassMachine failures."""


class ConfigurationError(GlassMachineError):
    """Raised when a circuit or experiment is structurally invalid."""


class SimulationError(GlassMachineError):
    """Raised when the simulation cannot continue safely."""


class UnstableSimulationError(SimulationError):
    """Raised when a circuit does not settle within the event budget."""


class ReplayMismatchError(GlassMachineError):
    """Raised when a deterministic replay differs from its recorded run."""


class ValidationError(GlassMachineError):
    """Raised when independent models disagree."""
