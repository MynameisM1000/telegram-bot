import os
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bot_token: str
    webhook_url: str = ""
    google_credentials_file: str = ""
    google_credentials_json: str | None = None
    spreadsheet_id: str
    admin_id: int
    sales_group_id: int | None = None
    attendance_group_id: int | None = None
    timezone: str = "Asia/Almaty"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("sales_group_id", "attendance_group_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return int(v)

settings = Settings()
