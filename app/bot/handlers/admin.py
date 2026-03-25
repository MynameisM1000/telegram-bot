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
        lines.append(f"Филиал {num}: {data['name']} (Адрес: {', '.join(data['aliases'])})")
    await message.reply("\n".join(lines) if len(lines) > 1 else "Нет данных")
    
@router.message(F.text == "📊 Сводка", F.from_user.id == settings.admin_id)
async def admin_summary_today(message: Message, gs):
    import datetime
    tz = datetime.timezone(datetime.timedelta(hours=5))
    today_str = datetime.datetime.now(tz).strftime("%d.%m.%Y")
    await generate_and_send_summary(message, gs, today_str)

@router.message(F.text.lower().startswith("сводка "), F.from_user.id == settings.admin_id)
async def admin_summary_date(message: Message, gs):
    date_str = message.text[7:].strip()
    await generate_and_send_summary(message, gs, date_str)

async def generate_and_send_summary(message: Message, gs, date_str: str):
    branches = gs.get_branches()
    summary = gs.get_daily_summary(date_str, branches)
    
    if not summary:
        await message.reply("Не удалось получить сводку или произошла ошибка.")
        return
        
    lines = [f"📊 Сводка за {date_str}"]
    lines.append(f"Итоговая касса: {summary['total_cash']} тг\n")
    
    lines.append("✅ Сдали:")
    if summary['submitted']:
        for b_num, b_sum in summary['submitted'].items():
            b_name = branches.get(str(b_num), {}).get('name', 'Неизвестно')
            lines.append(f"Ф-л {b_num} ({b_name}): {b_sum} тг")
    else:
        lines.append("Никто не сдал.")
        
    lines.append("\n❌ НЕ сдали (Красная зона):")
    if summary['not_submitted']:
        for ns in summary['not_submitted']:
            lines.append(f"• {ns}")
    else:
        lines.append("Все сдали!")
        
    await message.reply("\n".join(lines))
    
@router.message(F.text == "🔔 Напоминание", F.from_user.id == settings.admin_id)
async def admin_reminder(message: Message):
    if settings.sales_group_id:
        await message.bot.send_message(settings.sales_group_id, "⚠️ Напоминание! Не все сдали отчёт... Пожалуйста, сдайте!")
        await message.reply("Уведомление отправлено в группу.")
    else:
         await message.reply("ID группы выдач не настроен.")
          
