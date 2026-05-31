from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, time_limit: int = 2) -> None:
        self.cache = TTLCache(maxsize=10000, ttl=time_limit)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Basit bir bellek içi cache kullanarak Redis'ten bağımsız çalışmasını sağlıyoruz
        user_id = event.from_user.id
        if user_id in self.cache:
            return
        self.cache[user_id] = True
        return await handler(event, data)
