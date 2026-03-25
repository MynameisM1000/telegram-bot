import aiohttp
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from app.config import settings

async def ping_server():
    if not settings.webhook_url:
        return
    # Base URL is usually the webhook url without /webhook path, or just ping the root '/'
    base_url = settings.webhook_url.replace("/webhook", "")
    if not base_url.endswith("/"):
        base_url += "/"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as response:
                logging.info(f"Ping successful: {response.status}")
    except Exception as e:
        logging.error(f"Ping failed: {e}")

def send_daily_reminder(bot: Bot):
    if settings.sales_group_id:
        bot.loop.create_task(
            bot.send_message(settings.sales_group_id, "⚠️ Напоминание! Ежедневная проверка. Пожалуйста, сдайте отчёты, если еще не сделали это!")
        )

def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    
    # Запуск в 22:30 каждый день
    scheduler.add_job(
        send_daily_reminder, 
        trigger='cron', 
        hour=22, 
        minute=30, 
        kwargs={'bot': bot}
    )
    
    # Ping server every 5 minutes to keep Render alive
    if settings.webhook_url:
        scheduler.add_job(
            ping_server,
            trigger='interval',
            minutes=5
        )
    
    scheduler.start()
    return scheduler
