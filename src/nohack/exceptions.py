"""Domain-specific errors for No Hack."""


class NoHackError(Exception):
    """Base exception for controlled application failures."""


class ConfigurationError(NoHackError, ValueError):
    """The local configuration is invalid or unsafe."""
