from __future__ import annotations

from typing import Annotated

from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request, status

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/telegram")
async def telegram_webhook(
    request: Request,
    telegram_secret: Annotated[
        str | None,
        Header(alias="X-Telegram-Bot-Api-Secret-Token"),
    ] = None,
) -> dict[str, bool]:
    settings = request.app.state.settings
    if settings.telegram_webhook_secret and telegram_secret != settings.telegram_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Telegram webhook secret.",
        )

    payload = await request.json()
    bot = request.app.state.telegram_bot
    dispatcher = request.app.state.telegram_dispatcher
    update = Update.model_validate(payload, context={"bot": bot})
    await dispatcher.feed_update(bot, update)
    return {"ok": True}
