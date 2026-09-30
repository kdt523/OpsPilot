"""Application settings. The only place environment variables are read (OPSPILOT_* prefix)."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration (SPEC section 6.3)."""

    model_config = SettingsConfigDict(env_prefix="OPSPILOT_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://opspilot:opspilot@postgres:5432/opspilot"
    redis_url: str = "redis://redis:6379/0"

    gemini_api_key: str = ""
    llm_primary_model: str = "gemini-2.5-flash"
    llm_fallback_model: str = "gemini-2.5-flash-lite"
    llm_rpm: int = 8
    llm_daily_cap: int = 200
    llm_thinking_budget: int = 1024
    llm_temperature: float = 0.2
    llm_mode: Literal["live", "record", "replay"] = "live"

    max_steps: int = 12
    max_tokens: int = 60000
    max_seconds: int = 120
    confidence_threshold: float = Field(default=0.6, ge=0, le=1)

    webhook_token: str = ""
    prometheus_url: str = "http://kube-prometheus-stack-prometheus.monitoring.svc:9090"
    probe_url: str = "http://opspilot-probe.opspilot.svc:8080"
    target_namespaces: str = "demo"

    slack_bot_token: str = ""
    slack_app_token: str = ""
    slack_channel: str = "#incidents"
    github_token: str = ""
    github_repo: str = "kdt523/opspilot"

    auto_approve: bool = False
    verify_seconds: int = 180
    public_url: str = "http://localhost:8080"

    @property
    def target_namespace_list(self) -> list[str]:
        """Comma-separated OPSPILOT_TARGET_NAMESPACES as a list."""
        return [n.strip() for n in self.target_namespaces.split(",") if n.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor."""
    return Settings()
