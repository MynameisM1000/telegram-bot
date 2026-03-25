from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from app.config import settings

router = Router()

def get_admin_keyboard():
    kb = [
        [KeyboardButton(text="📊 Сводка"), KeyboardButton(text="🔔 Напоминание")],
        [KeyboardButton(text="▶️ Запустить бота"), KeyboardButton(text="⏸ Остановить бота")],
        [KeyboardButton(text="📡 Статус"), KeyboardButton(text="📋 Список филиалов")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@router.message(Command("start"), F.from_user.id == settings.admin_id)
async def admin_start(message: Message):
    await message.reply("Приветствую, Шеф! Панель управления активирована.", reply_markup=get_admin_keyboard())

@router.message(F.text == "📡 Статус", F.from_user.id == settings.admin_id)
async def admin_status(message: Message, bot_state: dict):
    is_active = bot_state.get('active', True)
    status_text = "🟢 Бот активен" if is_active else "🔴 Бот остановлен"
    await message.reply(status_text)

@router.message(F.text == "⏸ Остановить бота", F.from_user.id == settings.admin_id)
async def admin_stop(message: Message, bot_state: dict):
    bot_state['active'] = False
    await message.reply("🔴 Бот остановлен (не будет реагировать на отчеты)")

@router.message(F.text == "▶️ Запустить бота", F.from_user.id == settings.admin_id)
async def admin_start_bot(message: Message, bot_state: dict):
    bot_state['active'] = True
    await message.reply("🟢 Бот запущен")

@router.message(F.text == "📋 Список филиалов", F.from_user.id == settings.admin_id)
async def admin_branches(message: Message, gs):
    branches = gs.get_branches()
    lines = ["Список филиалов:"]
    for num, data in branches.items():
        lines.append(f"Филиал {num}: {data['name']} (Алиасы: {', '.join(data['aliases'])})")
    await message.reply("\n".join(lines) if len(lines) > 1 else "Нет данных")
    
@router.message(F.text == "📊 Сводка", F.from_user.id == settings.admin_id)
async def admin_summary(message: Message):
    # Упрощенная заглушка (в реальной задаче нужно запросить Табель выдач за сегодня и найти кто не сдал)
    await message.reply("📊 Сводка за сегодня:\nВ разработке... (потребует чтения Табеля)")
    
@router.message(F.text == "🔔 Напоминание", F.from_user.id == settings.admin_id)
async def admin_reminder(message: Message):
    if settings.sales_group_id:
        await message.bot.send_message(settings.sales_group_id, "⚠️ Напоминание! Не все сдали отчёт... Пожалуйста, сдайте!")
        await message.reply("Уведомление отправлено в группу.")
    else:
         await message.reply("ID группы выдач не настроен.")
          
