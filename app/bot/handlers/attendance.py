import re
import datetime
from aiogram import Router, F
from aiogram.types import Message
from app.config import settings

router = Router()

@router.message(F.chat.id == settings.attendance_group_id)
async def handle_attendance_group_message(message: Message, gs):
    if not message.text:
        return

    text_lower = message.text.lower()
    employees = gs.get_employees()
    
    # 1. Поиск сотрудника
    employee_name = None
    default_branch = None
    
    for emp_key, data in employees.items():
        # emp_key usually holds full name, we might just search for last name if needed,
        # but for simplicity let's search for exact name or first name/last name in the text.
        parts = emp_key.split()
        for part in parts:
            if len(part) > 2 and part in text_lower:
                employee_name = data['name']
                default_branch = data['branch']
                break
        if employee_name:
            break
            
    if not employee_name:
        return # Не сотрудник или нет в базе

    # 2. Определение филиала
    branch_num = str(default_branch)
    status_mark = "✓"
    is_replacement = False

    if "замена" in text_lower:
        is_replacement = True
        match = re.search(r'(?:замена.*?(?:на|филиал|№|\s))\s*(\d+)', text_lower)
        if match:
            branch_num = str(match.group(1))
            status_mark = branch_num
        else:
            status_mark = "Замена"

    # Запись
    tz = datetime.timezone(datetime.timedelta(hours=5))
    now = datetime.datetime.now(tz)
    date_str = now.strftime("%d.%m.%Y")
    time_str = now.strftime("%H:%M")

    archive_row = [date_str, time_str, employee_name, branch_num, message.text]
    gs.add_attendance_archive(archive_row)
    gs.update_attendance_timesheet(date_str, employee_name, status_mark)

    reply_text = f"✅ Явка: {employee_name} "
    if is_replacement:
        reply_text += f"(замена → {branch_num})"
    else:
        reply_text += f"({branch_num})"

    await message.reply(reply_text)
