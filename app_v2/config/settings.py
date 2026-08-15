"""Các giá trị cấu hình nền tảng của V2.

Giai đoạn 1 cố ý không đọc biến môi trường hay API key.
"""

from dataclasses import dataclass, field
from typing import Literal

DEFAULT_MAX_CHARS = 12_000
ProviderName = Literal["mock", "gemini", "openai", "deepseek"]


@dataclass(frozen=True, slots=True)
class ProviderSettings:
    """Cấu hình provider; API key vẫn chỉ được đọc từ environment khi cần gọi."""

    provider: ProviderName = "mock"
    model: str | None = None
    source_language: str = "English"
    target_language: str = "Vietnamese"

    @property
    def resolved_model(self) -> str:
        defaults = {
            "mock": "mock-echo-v1",
            "gemini": "gemini-2.5-flash",
            "openai": "gpt-default",
            "deepseek": "deepseek-default",
        }
        return self.model or defaults[self.provider]

    @property
    def api_key_environment_variable(self) -> str | None:
        return {
            "mock": None,
            "gemini": "GEMINI_API_KEY",
            "openai": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }[self.provider]


@dataclass(frozen=True, slots=True)
class V2Settings:
    """Cấu hình thuần cho luồng PDF; có thể mở rộng ở các giai đoạn sau."""

    source_language: str = "English"
    target_language: str = "Vietnamese"
    default_chunk_characters: int = DEFAULT_MAX_CHARS
    require_text_layer: bool = True
    page_number_base: int = 0
    provider: ProviderSettings = field(default_factory=ProviderSettings)
