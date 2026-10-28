"""Event hook / plug-in system."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Callable, Dict, List

Handler = Callable[..., Any]


class EventBus:
    def __init__(self) -> None:
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)

    def on(self, event: str) -> Callable[[Handler], Handler]:
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
        handlers = self._handlers.get(event, [])
        if not handlers:
            return

        errors: List[BaseException] = []
        for handler in handlers:
            try:
                result = handler(**kwargs)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:
                errors.append(exc)

        if errors:
            raise RuntimeError(
                f"{len(errors)} handler(s) failed for event {event!r}"
            ) from errors[0]


event_bus = EventBus()


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