"""Application settings loaded from environment variables / credentials.env."""

from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": "credentials.env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # Deepgram
    deepgram_api_key: str = ""

    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = ""  # Leave empty for standard OpenAI API; set for custom gateway

    # Anthropic
    anthropic_api_key: str = ""
    claude_bearer_token: str = ""  # For AWS Bedrock auth (optional, legacy)

    # Google Gemini
    gemini_api_key: str = Field(
        default="", validation_alias=AliasChoices("gemini_api_key", "google_api_key")
    )

    # PRISMtrace (live LLM traces). Auth header is X-PRISMtrace-Key, not Bearer.
    prismtrace_api_key: str = ""
    prismtrace_project_id: str = ""
    prismtrace_host: str = "https://prism.blockconvey.com"

    # ElevenLabs TTS
    elevenlabs_api_key: str = ""
    elevenlabs_voice_sales: str = "EXAVITQu4vr4xnSDxMaL"  # Sarah
    elevenlabs_voice_customer: str = "CwhRBWXzGAHq8TQ4Fs17"  # Roger

    # LLM selection
    llm_provider: str = "openai"  # "openai", "anthropic", or "gemini"
    llm_model: str = "gpt-4o"

    # Database
    db_path: str = "data/sales_copilot.db"


settings = Settings()
