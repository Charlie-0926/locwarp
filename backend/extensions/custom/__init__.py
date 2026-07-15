from extensions.registry import ExtensionRegistry

from .spiral import register as register_spiral


def register_custom_extensions(registry: ExtensionRegistry) -> None:
    register_spiral(registry)
