from extensions.registry import ExtensionRegistry

from .handler import SpiralWalkHandler

EXTENSION_ID = "spiral"


def register(registry: ExtensionRegistry) -> None:
    registry.register(EXTENSION_ID, SpiralWalkHandler)
