import pytest
from pydantic import ValidationError

from voiceserve_common.settings import CommonSettings


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("LANG_STRATEGY", "REPLAY_MODE", "DAILY_BUDGET_USD", "ENVIRONMENT"):
        monkeypatch.delenv(var, raising=False)
    settings = CommonSettings()
    assert settings.lang_strategy == "hybrid"
    assert settings.replay_mode is False
    assert settings.daily_budget_usd == 5.0
    assert settings.environment == "dev"


def test_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANG_STRATEGY", "native")
    monkeypatch.setenv("REPLAY_MODE", "true")
    monkeypatch.setenv("DAILY_BUDGET_USD", "2.5")
    settings = CommonSettings()
    assert settings.lang_strategy == "native"
    assert settings.replay_mode is True
    assert settings.daily_budget_usd == 2.5


@pytest.mark.parametrize(
    ("var", "value"),
    [("LANG_STRATEGY", "english"), ("DAILY_BUDGET_USD", "-1"), ("ENVIRONMENT", "staging")],
)
def test_rejects_invalid_values(monkeypatch: pytest.MonkeyPatch, var: str, value: str) -> None:
    monkeypatch.setenv(var, value)
    with pytest.raises(ValidationError):
        CommonSettings()
