"""Small extension registry used by the custom thin-fork layer."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

HandlerFactory = Callable[[Any], Any]


class ExtensionHandlers:
    """Engine-bound handler collection with fail-fast lookups."""

    def __init__(self, handlers: Mapping[str, Any]) -> None:
        self._handlers = dict(handlers)

    def require(self, extension_id: str) -> Any:
        try:
            return self._handlers[extension_id]
        except KeyError as exc:
            raise RuntimeError(f"Required extension is not registered: {extension_id}") from exc


class ExtensionRegistry:
    """Register handler factories without coupling them to SimulationEngine."""

    def __init__(self) -> None:
        self._factories: dict[str, HandlerFactory] = {}

    def register(self, extension_id: str, factory: HandlerFactory) -> None:
        if extension_id in self._factories:
            raise ValueError(f"Duplicate extension id: {extension_id}")
        self._factories[extension_id] = factory

    def bind(self, engine: Any) -> ExtensionHandlers:
        return ExtensionHandlers({
            extension_id: factory(engine)
            for extension_id, factory in self._factories.items()
        })
