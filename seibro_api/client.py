"""Compatibility imports for the SEIBRO OpenPlatform client."""

from .openapi import SeibroAPIError, SeibroClient, retry_transient

__all__ = ["SeibroClient", "SeibroAPIError", "retry_transient"]
