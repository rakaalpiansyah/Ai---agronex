"""Domain and business logic exceptions for the crop recommendation engine."""


class AgronomyEngineError(Exception):
    """Base domain exception."""
    pass


class InsufficientTelemetryError(AgronomyEngineError):
    """Raised when available telemetry data does not meet minimum completeness."""
    pass


class InvalidSensorReadingError(AgronomyEngineError):
    """Raised when an individual sensor reading violates physical limits."""
    pass


class CropNotFoundError(AgronomyEngineError):
    """Raised when a requested crop is absent from the knowledge base."""
    pass


class CalibrationError(AgronomyEngineError):
    """Raised when calibration curve parameters cannot be solved."""
    pass
