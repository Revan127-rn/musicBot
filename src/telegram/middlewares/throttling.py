from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from cachetools import TTLCache


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self.caches = {
            "message": TTLCache(maxsize=10_000, ttl=rate_limit),
            "callback_query": TTLCache(maxsize=10_000, ttl=rate_limit),
        }

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        if isinstance(event, Message):
            cache = self.caches["message"]
            event_type = "message"
        elif isinstance(event, CallbackQuery):
            cache = self.caches["callback_query"]
            event_type = "callback_query"
        else:
            return await handler(event, data)

        if user_id in cache:
            # User is throttled, ignore the event
            if event_type == "message":
                await event.answer("Çok hızlısın! Lütfen biraz yavaşla.")
            elif event_type == "callback_query":
                await event.answer("Çok hızlısın! Lütfen biraz yavaşla.", show_alert=True)
            return

        cache[user_id] = None  # Add user to cache
        return await handler(event, data)
