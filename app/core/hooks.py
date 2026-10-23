"""Event hook / plug-in system.

Domain-specific behaviour can be attached to core lifecycle events without
modifying core code. Handlers are simple (sync or async) callables:

    from app.core.hooks import event_bus

    @event_bus.on("client.after_create")
    def notify_slack(client):
        ...

    await event_bus.emit("client.after_create", client=client)
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Union

Handler = Callable[..., Any]


class EventBus:
    """A small in-process pub/sub bus keyed by event name.

    Multiple handlers may register for the same event; they run in registration
    order. Async handlers are awaited, sync handlers are called directly.
    Exceptions raised by a handler do not stop other handlers — they are
    collected and re-raised as a single `RuntimeError` if any failed.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)

    def on(self, event: str) -> Callable[[Handler], Handler]:
        """Decorator to register a handler for an event."""

        def decorator(handler: Handler) -> Handler:
            self.subscribe(event, handler)
            return handler

        return decorator

    def subscribe(self, event: str, handler: Handler) -> None:
        self._handlers[event].append(handler)

    def unsubscribe(self, event: str, handler: Handler) -> None:
        self._handlers[event] = [
            h for h in self._handlers.get(event, []) if h is not handler
        ]

    def has_handlers(self, event: str) -> bool:
        return bool(self._handlers.get(event))

    async def emit(self, event: str, **kwargs: Any) -> None:
        """Emit an event to all registered handlers.

        Args:
            event: Event name, e.g. ``client.after_create``.
            **kwargs: Context passed to every handler.
        """
        handlers = self._handlers.get(event, [])
        if not handlers:
            return

        errors: List[BaseException] = []
        for handler in handlers:
            try:
                result = handler(**kwargs)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(exc)

        if errors:
            raise RuntimeError(
                f"{len(errors)} handler(s) failed for event {event!r}"
            ) from errors[0]


#: Global event bus used by core services. Plug domain handlers into this.
event_bus = EventBus()


# --- Standard event names (core services emit these) ---

CLIENT_BEFORE_CREATE = "client.before_create"
CLIENT_AFTER_CREATE = "client.after_create"
CLIENT_BEFORE_UPDATE = "client.before_update"
CLIENT_AFTER_UPDATE = "client.after_update"
CLIENT_BEFORE_DELETE = "client.before_delete"
CLIENT_AFTER_DELETE = "client.after_delete"

INTERACTION_AFTER_CREATE = "interaction.after_create"
TASK_AFTER_CREATE = "task.after_create"
TASK_AFTER_STATUS_CHANGE = "task.after_status_change"
DOCUMENT_AFTER_UPLOAD = "document.after_upload"