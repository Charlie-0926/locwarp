"""Bootstrap for all locally maintained extensions."""

from typing import Any

from .custom import register_custom_extensions
from .registry import ExtensionHandlers, ExtensionRegistry


def build_extension_handlers(engine: Any) -> ExtensionHandlers:
    registry = ExtensionRegistry()
    register_custom_extensions(registry)
    return registry.bind(engine)
