"""Custom exception hierarchy for clearcut."""

from __future__ import annotations


class ClearCutError(Exception):
    """Base exception for all clearcut errors."""


class FileError(ClearCutError):
    """File not found or inaccessible."""


class AudioError(ClearCutError):
    """Audio processing failure."""


class EncodingError(ClearCutError):
    """Video encoding failure."""


class ConfigError(ClearCutError):
    """Invalid configuration."""


class CaptionError(ClearCutError):
    """Caption generation or burn-in failure."""


class LLMError(ClearCutError):
    """LLM (Claude CLI) communication failure."""
