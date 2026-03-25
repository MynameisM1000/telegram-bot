import re
import datetime
from aiogram import Router, F
from aiogram.types import Message
from app.config import settings

router = Router()

def parse_sales_report(text: str, branches: dict):
    text_lower = text.lower()
    branch_num = None
    
    # 1. Поиск филиала
    match = re.search(r'(?:филиал|ф-л|№)\s*(\d+)', text_lower)
    if match:
        branch_num = match.group(1)
    else:
        # Поиск по алиасам в первых 3 строках
        lines = text_lower.split('\n')[:3]
        for num, data in branches.items():
            for alias in data['aliases']:
                for line in lines:
                    if alias in line:
                        branch_num = num
                        break
                if branch_num: break
            if branch_num: break

    if not branch_num or str(branch_num) not in branches:
        return None, "Филиал не распознан"

    result = {
        "branch": str(branch_num),
        "branch_name": branches[str(branch_num)]['name'],
        "total_sum": 0,
        "items": {}
    }

    # 2. Одиночные значения
    single_fields = ["приход", "клиентов", "оформлено", "отказ"]
    for field in single_fields:
        match = re.search(rf'{field}.*?(\d[0-9\s\.]*)', text_lower)
        if match:
             digits = re.sub(r'[^\d]', '', match.group(1))
             result["items"][field] = int(digits) if digits else 0
        else:
             result["items"][field] = 0

    blocks = ["ношение", "залог", "скупка", "продление", "выкуп"]
    lines = text_lower.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        for block in blocks:
            if line.startswith(block[:5]): 
                count_match = re.search(r'(\d[0-9\s\.]*)', line.replace(block[:5], ''))
                count = 0
                if count_match:
                     cdigits = re.sub(r'[^\d]', '', count_match.group(1))
                     count = int(cdigits) if cdigits else 0
                
                sum_val = 0
                for j in range(1, 4):
                    if i + j < len(lines):
                        next_line = lines[i + j].lower()
                        if "сумма" in next_line:
                            clean_line = next_line.replace('сумма', '')
                            val_match = re.search(r'(\d[0-9\s\.]*)', clean_line)
                            if val_match:
                                sdigits = re.sub(r'[^\d]', '', val_match.group(1))
                                if sdigits:
                                    sum_val = int(sdigits)
                            break
                
                result["items"][block] = {"count": count, "sum": sum_val}

    # 4. Общая сумма
    total_match = re.search(r'общ[аяе].*?(\d[0-9\s\.]*)', text_lower.replace('\n', ' '))
    if total_match:
        digits = re.sub(r'[^\d]', '', total_match.group(1))
        if digits:
            result["total_sum"] = int(digits)

    if result["total_sum"] <= 0:
         return None, "Общая сумма не найдена или равна 0"

    return result, "OK"

@router.message(F.chat.id == settings.sales_group_id)
async def handle_sales_group_message(message: Message, gs):
    if not message.text:
        return

    print(f"\n[ТЕРМИНАЛ] 📥 Получено новое сообщение в Группу Выдач:\n{message.text[:100]}...\n")

    branches = gs.get_branches()
    parsed_data, error = parse_sales_report(message.text, branches)

    if not parsed_data:
        print(f"[ТЕРМИНАЛ] ❌ Сообщение не распознано как отчет. Причина: {error}")
        # Пересылаем админу, если похоже на отчет, но не распознан
        if "сумма" in message.text.lower() or "приход" in message.text.lower():
            await message.bot.send_message(settings.admin_id, f"⚠️ Не распознан отчёт:\n\n{message.text}\n\nОшибка: {error}")
        return

    # Защита от дубликатов
    tz = datetime.timezone(datetime.timedelta(hours=5)) # Almaty/Tashkent
    now = datetime.datetime.now(tz)
    date_str = now.strftime("%d.%m.%Y")
    time_str = now.strftime("%H:%M")

    is_dup = gs.check_sales_duplicate(date_str, parsed_data['branch'])
    if is_dup:
        print(f"[ТЕРМИНАЛ] ⚠️ Заблокирован дубликат отчета от Филиала {parsed_data['branch']} за сегодня.")
        await message.reply("⚠️ Дубликат! Отчет за сегодня уже сдан.")
        return

    # Подготовка данных для архива
    # Формат: Дата, Время, Филиал
    archive_row = [date_str, time_str, parsed_data['branch'], parsed_data['total_sum'], message.text]
    gs.add_sales_archive(archive_row)
    
    # Табель
    gs.update_sales_timesheet(date_str, parsed_data['branch'], parsed_data['total_sum'])

    reply_text = (
        f"✅ Отчёт принят!\n"
        f"Филиал: {parsed_data['branch']} ({parsed_data['branch_name']})\n"
        f"Общая сумма: {parsed_data['total_sum']}"
    )
    print(f"[ТЕРМИНАЛ] ✅ Отчет успешно записан в Таблицу! (Филиал {parsed_data['branch']}, Сумма: {parsed_data['total_sum']})")
    await message.reply(reply_text)
