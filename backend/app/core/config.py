from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # API related settings
    API_V1_STR: str = Field("/api", description="API prefix for version 1")
    ENV: str = Field(
        "dev", description="Application environment (dev, staging, production)"
    )

    # Supabase settings
    DATABASE_URI: str = Field(..., description="Database URI for SQLAlchemy")
    SUPABASE_URL: str = Field(..., description="Supabase Instant URL")
    SUPABASE_SECRET_KEY: str = Field(..., description="Secret key for Supabase")
    SUPABASE_ANON_KEY: str = Field(
        ..., description="client side secrete key for supabase"
    )
    ECHO_SQL: bool = Field(False, description="Whether to echo SQL queries")

    # Server settings
    SERVER_PORT: int = Field(9213, description="Port on which the server runs")

    # Admin settings just used for create_superadmin.py
    SUPERADMIN_EMAIL: str
    SUPERADMIN_PASSWORD: str
    # General settings
    PROJECT_NAME: str = Field("Nafees", description="Name of the project")

    # Sentry settings
    SENTRY_DSN: Optional[str] = Field(None, description="DSN for Sentry error tracking")

    # LLM settings
    # OPENAI_API_KEY: str = Field(..., description="API key for OpenAI")

    class ConfigDict:
        case_sensitive = True
        env_file = ".env"
        json_encoders = {SecretStr: lambda v: v.get_secret_value() if v else None}

    # @field_validator(
        
    # )
    # @classmethod
    # def not_empty(cls, v, field):
    #     if isinstance(v, SecretStr):
    #         if not v.get_secret_value():
    #             raise ValueError(f"{field.name} cannot be empty")
    #     else:
    #         if not v:
    #             raise ValueError(f"{field.name} cannot be empty")
    #     return v


# Initialize the settings
settings = Settings()
