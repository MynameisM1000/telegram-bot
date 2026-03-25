from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from app.config import settings

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
    
    scheduler.start()
    return scheduler
