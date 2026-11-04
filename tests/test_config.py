from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from kronostrading.config import AppConfig, Secrets, load_config

DEFAULT = Path(__file__).resolve().parents[1] / "config" / "default.yaml"


def _raw() -> dict[str, Any]:
    with DEFAULT.open(encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)
    return data


def test_default_config_loads() -> None:
    cfg = load_config(DEFAULT)
    assert cfg.account.capital == 10_000
    assert cfg.risk.risk_per_trade == 100
    assert cfg.kronos.model_id == "NeoQuasar/Kronos-small"
    assert cfg.benchmark in {i.id for i in cfg.instruments}
    assert all(i.enabled for i in cfg.enabled_instruments)


def test_default_config_warns_about_unverified_fees() -> None:
    cfg = load_config(DEFAULT)
    assert any("unverified fees" in w for w in cfg.warnings())


def test_model_tokenizer_mismatch_rejected() -> None:
    raw = _raw()
    raw["kronos"]["model_id"] = "NeoQuasar/Kronos-mini"  # needs Tokenizer-2k
    with pytest.raises(ValidationError, match="requires tokenizer"):
        AppConfig.model_validate(raw)


def test_large_model_not_available() -> None:
    raw = _raw()
    raw["kronos"]["model_id"] = "NeoQuasar/Kronos-large"  # not open-source
    with pytest.raises(ValidationError, match="Unknown Kronos model"):
        AppConfig.model_validate(raw)


def test_context_above_model_limit_rejected() -> None:
    raw = _raw()
    raw["kronos"]["max_context"] = 1024
    with pytest.raises(ValidationError, match="max_context"):
        AppConfig.model_validate(raw)


def test_excessive_risk_rejected() -> None:
    raw = _raw()
    raw["risk"]["risk_per_trade"] = 600.0  # 6% of 10k
    raw["risk"]["max_open_risk"] = 1200.0
    with pytest.raises(ValidationError, match="5% of capital"):
        AppConfig.model_validate(raw)


def test_unknown_broker_profile_rejected() -> None:
    raw = _raw()
    raw["instruments"][0]["broker_profile"] = "nope"
    with pytest.raises(ValidationError, match="unknown broker_profile"):
        AppConfig.model_validate(raw)


def test_unknown_keys_rejected() -> None:
    raw = _raw()
    raw["risk"]["typo_field"] = 1
    with pytest.raises(ValidationError):
        AppConfig.model_validate(raw)


def test_secrets_are_masked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KT_TELEGRAM_BOT_TOKEN", "123:very-secret")
    s = Secrets(_env_file=None)  # type: ignore[call-arg]
    assert s.telegram_bot_token is not None
    assert "very-secret" not in repr(s)
    assert s.telegram_bot_token.get_secret_value() == "123:very-secret"
