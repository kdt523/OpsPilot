"""Phase 0 smoke test: every module in app/ imports cleanly."""

import importlib
import pkgutil

import app


def test_all_modules_import() -> None:
    names = [m.name for m in pkgutil.walk_packages(app.__path__, "app.")]
    assert len(names) > 30
    for name in names:
        importlib.import_module(name)


def test_settings_defaults() -> None:
    from app.config import Settings

    s = Settings()
    assert s.target_namespace_list == ["demo"]
    assert s.llm_primary_model == "gemini-2.5-flash"
