"""Entry point tối thiểu cho V2."""

from app_v2.config.settings import V2Settings


def main() -> int:
    """Xác nhận package V2 có thể được nạp mà không cần AI hoặc GUI."""
    settings = V2Settings()
    print(f"app_v2 ready (languages: {settings.source_language} -> {settings.target_language}).")
    print("Phase 1 provides PDF models and reading foundations only; no AI or Word export.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
