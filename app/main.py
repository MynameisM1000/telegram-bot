from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, types
from app.config import settings
from app.services.google_sheets import GoogleSheetsService
from app.bot.handlers import sales, attendance, admin
from app.services.scheduler import setup_scheduler

# Инициализация сервисов
gs_service = GoogleSheetsService(
    credentials_file=settings.google_credentials_file,
    credentials_json=settings.google_credentials_json,
    spreadsheet_id=settings.spreadsheet_id
)

bot = Bot(token=settings.bot_token)
dp = Dispatcher()

# Общее состояние бота (запущен/остановлен)
bot_state = {"active": True}

# Прокидываем сервисы в обработчики
dp["gs"] = gs_service
dp["bot_state"] = bot_state

# Регистрация роутеров только если они еще не добавлены
if not dp.sub_routers:
    dp.include_router(admin.router)
    dp.include_router(sales.router)
    dp.include_router(attendance.router)

scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global scheduler
    scheduler = setup_scheduler(bot)
    
    if settings.webhook_url:
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url != settings.webhook_url:
            await bot.set_webhook(url=settings.webhook_url)
        print(f"Webhook set to {settings.webhook_url}")
    else:
        # Запуск local polling
        import asyncio
        print("Webhook URL is not set. Bypassing Webhook, starting local long-polling...")
        # Удаляем вебхук на всякий случай перед поллингом
        await bot.delete_webhook(drop_pending_updates=True)
        asyncio.create_task(dp.start_polling(bot))

    yield

    # Shutdown
    if settings.webhook_url:
        await bot.delete_webhook()
    if scheduler:
        scheduler.shutdown()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def telegram_webhook(request: Request):
    if not bot_state["active"]:
        return {"status": "paused"}
        
    try:
        update_data = await request.json()
        update = types.Update(**update_data)
        await dp.feed_update(bot=bot, update=update)
        return {"status": "ok"}
    except Exception as e:
        print(f"Ошибка при обработке вебхука: {e}")
        raise HTTPException(status_code=500, detail="Internal error")

@app.get("/")
def root():
    return {"status": "Lombard Bot is running"}
