import gspread
from google.oauth2.service_account import Credentials
import os

class GoogleSheetsService:
    def __init__(self, credentials_file: str, spreadsheet_id: str, credentials_json: str | None = None):
        self.credentials_file = credentials_file
        self.credentials_json = credentials_json
        self.spreadsheet_id = spreadsheet_id
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        if self.credentials_json:
            import json
            info = json.loads(self.credentials_json)
            credentials = Credentials.from_service_account_info(info, scopes=scopes)
        else:
            if not os.path.isabs(self.credentials_file):
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                self.credentials_file = os.path.join(base_dir, self.credentials_file)
            credentials = Credentials.from_service_account_file(self.credentials_file, scopes=scopes)
            
        self.client = gspread.authorize(credentials)
        self.sheet = self.client.open_by_key(self.spreadsheet_id)

    def get_branches(self):
        """Возвращает список филиалов и их алиасы."""
        try:
            worksheet = self.sheet.worksheet("Филиалы")
            records = worksheet.get_all_records()
            branches = {}
            for row in records:
                number = str(row.get('Номер', '')).strip()
                if not number:
                    continue
                name = str(row.get('Название', '')).strip()
                aliases_raw = str(row.get('Псевдонимы (через запятую)', ''))
                aliases = [a.strip().lower() for a in aliases_raw.split(',') if a.strip()]
                branches[number] = {
                    'name': name,
                    'aliases': aliases
                }
            return branches
        except gspread.exceptions.WorksheetNotFound:
            print("Лист 'Филиалы' не найден.")
            return {}

    def get_employees(self):
        """Возвращает список сотрудников и их дефолтные филиалы."""
        try:
            worksheet = self.sheet.worksheet("Сотрудники")
            records = worksheet.get_all_records()
            employees = {}
            for row in records:
                name = str(row.get('ФИО Сотрудника', '')).strip()
                if not name:
                    continue
                branch = str(row.get('Филиал по умолчанию', '')).strip()
                employees[name.lower()] = {
                    'name': name,
                    'branch': branch
                }
            return employees
        except gspread.exceptions.WorksheetNotFound:
            print("Лист 'Сотрудники' не найден.")
            return {}

    def add_sales_archive(self, data: list):
        """Добавляет строку в Архив выдач."""
        try:
            worksheet = self.sheet.worksheet("Архив выдач")
            worksheet.append_row(data)
            return True
        except Exception as e:
            print(f"Ошибка записи в Архив выдач: {e}")
            return False

    def get_daily_summary(self, date_str: str, branches: dict):
        """Читает Архив выдач и формирует сводку кто сдал и сколько."""
        try:
            worksheet = self.sheet.worksheet("Архив выдач")
            records = worksheet.get_all_values()
            
            submitted = {}
            total_cash = 0
            
            for row in records[1:]:
                if len(row) >= 4:
                    row_date = str(row[0]).strip()
                    row_branch = str(row[2]).strip()
                    row_sum = str(row[3]).replace(' ', '').replace('.', '').replace(',', '').replace('тг', '')
                    
                    if row_date == date_str:
                        try:
                            sum_val = int(row_sum)
                        except ValueError:
                            sum_val = 0
                            
                        submitted[row_branch] = sum_val
                        total_cash += sum_val
                        
            not_submitted = []
            for b_num, b_data in branches.items():
                if str(b_num) not in submitted:
                    not_submitted.append(f"{b_num} ({b_data['name']})")
                    
            return {
                "submitted": submitted,
                "not_submitted": not_submitted,
                "total_cash": total_cash
            }
        except Exception as e:
            print(f"Ошибка сводки: {e}")
            return None

    def check_sales_duplicate(self, date_str: str, branch_number: str):
        """Проверяет, сдавал ли филиал отчет за дату."""
        try:
            worksheet = self.sheet.worksheet("Архив выдач")
            records = worksheet.get_all_values()
            for row in records[1:]: # Пропускаем заголовок
                if len(row) > 2:
                    row_date = row[0].strip()
                    row_branch = str(row[2]).strip()
                    if row_date == date_str and row_branch == branch_number:
                        return True
            return False
        except Exception:
            return False

    def update_sales_timesheet(self, date_str: str, branch_number: str, total_sum: int):
        """Обновляет табель выдач (пересечение дата/филиал)."""
        try:
            worksheet = self.sheet.worksheet("Табель выдач")
            row1 = worksheet.row_values(1)
            col_index = None
            for idx, val in enumerate(row1):
                if str(val).strip() == branch_number:
                    col_index = idx + 1
                    break
            
            if not col_index:
                return False
                
            col1 = worksheet.col_values(1)
            row_index = None
            for idx, val in enumerate(col1):
                if str(val).strip() == date_str:
                    row_index = idx + 1
                    break
                    
            if not row_index:
                return False
                
            worksheet.update_cell(row_index, col_index, total_sum)
            return True
        except Exception as e:
            print(f"Ошибка обновления Табель выдач: {e}")
            return False

    def add_attendance_archive(self, data: list):
        """Добавляет строку в Архив явки."""
        try:
            worksheet = self.sheet.worksheet("Архив явки")
            worksheet.append_row(data)
            return True
        except Exception as e:
            print(f"Ошибка записи в Архив явки: {e}")
            return False

    def update_attendance_timesheet(self, date_str: str, employee_name: str, status: str):
        """Обновляет табель явки (пересечение дата/ФИО)."""
        try:
            worksheet = self.sheet.worksheet("Табель явки")
            col1 = worksheet.col_values(1)
            row_index = None
            for idx, val in enumerate(col1):
                if str(val).strip().lower() == employee_name.lower():
                    row_index = idx + 1
                    break
                    
            if not row_index:
                return False
                
            row1 = worksheet.row_values(1)
            col_index = None
            for idx, val in enumerate(row1):
                if str(val).strip() == date_str:
                    col_index = idx + 1
                    break
            
            if not col_index:
                return False
                
            worksheet.update_cell(row_index, col_index, status)
            return True
        except Exception as e:
            print(f"Ошибка обновления Табель явки: {e}")
            return False
