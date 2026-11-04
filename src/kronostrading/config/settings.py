"""Typed configuration: YAML file validated with Pydantic, secrets loaded from environment/.env."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Facts taken from the Kronos README model zoo (third_party/Kronos/README.md).
# Kronos-large is not open-source, so it is intentionally absent.
KRONOS_MODEL_SPECS: dict[str, tuple[str, int]] = {
    "NeoQuasar/Kronos-mini": ("NeoQuasar/Kronos-Tokenizer-2k", 2048),
    "NeoQuasar/Kronos-small": ("NeoQuasar/Kronos-Tokenizer-base", 512),
    "NeoQuasar/Kronos-base": ("NeoQuasar/Kronos-Tokenizer-base", 512),
}


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AccountConfig(_Strict):
    capital: float = Field(gt=0)
    base_currency: str = "EUR"


class RiskConfig(_Strict):
    risk_per_trade: float = Field(gt=0)
    max_position_pct: float = Field(gt=0, le=1)
    max_open_risk: float = Field(gt=0)
    max_open_positions: int = Field(ge=1)
    max_drawdown_kill: float = Field(gt=0, lt=1)


class Instrument(_Strict):
    id: str
    name: str
    asset_class: Literal["etf", "etc", "stock"]
    data_symbol: str
    tv_symbol: str | None = None
    currency: str
    calendar: str
    broker_profile: str
    history_proxy: str | None = None
    enabled: bool = True


class BrokerProfile(_Strict):
    commission_fixed: float = Field(ge=0)
    commission_pct: float = Field(ge=0, lt=0.05)
    commission_min: float = Field(ge=0)
    fx_fee_pct: float = Field(ge=0, lt=0.05)
    spread_bps: float = Field(ge=0)
    slippage_bps: float = Field(ge=0)
    supports_stop_orders: bool = False
    verified: bool = False


class DataConfig(_Strict):
    cache_dir: Path = Path("var/cache")
    timeframe: Literal["1d"] = "1d"
    history_start: date
    primary_source: Literal["yfinance", "stooq", "eodhd"] = "yfinance"
    fallback_sources: list[Literal["yfinance", "stooq", "eodhd"]] = Field(default_factory=list)


class KronosConfig(_Strict):
    model_id: str
    tokenizer_id: str
    model_revision: str | None = None
    tokenizer_revision: str | None = None
    max_context: int = Field(gt=0)
    lookback: int = Field(gt=0)
    temperature: float = Field(gt=0)
    top_p: float = Field(gt=0, le=1)
    n_paths: int = Field(ge=1)
    device: str = "auto"
    seed: int = 42

    @model_validator(mode="after")
    def _check_model_tokenizer_pair(self) -> KronosConfig:
        spec = KRONOS_MODEL_SPECS.get(self.model_id)
        if spec is None:
            # Allow local fine-tuned checkpoints, but only if they are paths on disk.
            if not Path(self.model_id).exists():
                known = ", ".join(KRONOS_MODEL_SPECS)
                raise ValueError(f"Unknown Kronos model '{self.model_id}'. Known: {known}")
            return self
        tokenizer, ctx = spec
        if self.tokenizer_id != tokenizer:
            raise ValueError(
                f"{self.model_id} requires tokenizer {tokenizer}, got {self.tokenizer_id}"
            )
        if self.max_context > ctx:
            raise ValueError(
                f"{self.model_id} supports max_context <= {ctx}, got {self.max_context}"
            )
        return self


class SignalConfig(_Strict):
    horizon: int = Field(ge=1)
    atr_period: int = Field(ge=2)
    stop_atr_mult: float = Field(gt=0)
    min_reward_risk: float = Field(gt=0)
    min_expected_r: float
    max_atr_pct: float = Field(gt=0, lt=1)
    stop_mode: Literal["close", "intraday"] = "close"
    entry_expiry_bars: int = Field(ge=1)
    max_holding_bars: int = Field(ge=1)


class WalkForwardConfig(_Strict):
    train_years: int = Field(ge=1)
    test_months: int = Field(ge=1)
    step_months: int = Field(ge=1)


class BacktestConfig(_Strict):
    walk_forward: WalkForwardConfig
    holdout_start: date


class AlertsConfig(_Strict):
    telegram_enabled: bool = False
    slack_enabled: bool = False


class AppConfig(_Strict):
    account: AccountConfig
    risk: RiskConfig
    instruments: list[Instrument]
    benchmark: str
    broker_profiles: dict[str, BrokerProfile]
    data: DataConfig
    kronos: KronosConfig
    signals: SignalConfig
    backtest: BacktestConfig
    alerts: AlertsConfig = AlertsConfig()

    @field_validator("instruments")
    @classmethod
    def _unique_ids(cls, v: list[Instrument]) -> list[Instrument]:
        ids = [i.id for i in v]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise ValueError(f"Duplicate instrument ids: {sorted(dupes)}")
        return v

    @model_validator(mode="after")
    def _cross_checks(self) -> AppConfig:
        ids = {i.id for i in self.instruments}
        if self.benchmark not in ids:
            raise ValueError(f"benchmark '{self.benchmark}' is not an instrument id")
        for inst in self.instruments:
            if inst.broker_profile not in self.broker_profiles:
                raise ValueError(f"{inst.id}: unknown broker_profile '{inst.broker_profile}'")
        if self.risk.risk_per_trade > self.risk.max_open_risk:
            raise ValueError("risk_per_trade cannot exceed max_open_risk")
        if self.risk.risk_per_trade > 0.05 * self.account.capital:
            raise ValueError("risk_per_trade above 5% of capital is refused")
        if self.kronos.lookback > self.kronos.max_context:
            raise ValueError("kronos.lookback must not exceed kronos.max_context")
        return self

    @property
    def enabled_instruments(self) -> list[Instrument]:
        return [i for i in self.instruments if i.enabled]

    def warnings(self) -> list[str]:
        """Non-fatal issues the user should know about before trusting any result."""
        out: list[str] = []
        for name, prof in self.broker_profiles.items():
            if not prof.verified:
                out.append(
                    f"broker profile '{name}' has unverified fees (set verified: true once checked)"
                )
        if self.signals.stop_mode == "intraday":
            for inst in self.enabled_instruments:
                if not self.broker_profiles[inst.broker_profile].supports_stop_orders:
                    out.append(
                        f"{inst.id}: stop_mode=intraday but broker '{inst.broker_profile}' "
                        "is not marked as supporting stop orders"
                    )
        return out


class Secrets(BaseSettings):
    """Secrets and runtime paths from environment variables (KT_*) or .env. Never from YAML."""

    model_config = SettingsConfigDict(env_prefix="KT_", env_file=".env", extra="ignore")

    config_path: Path = Path("config/default.yaml")
    telegram_bot_token: SecretStr | None = None
    telegram_chat_id: str | None = None
    slack_webhook_url: SecretStr | None = None
    fred_api_key: SecretStr | None = None
    eodhd_api_key: SecretStr | None = None
    hf_token: SecretStr | None = None


def load_config(path: Path | str) -> AppConfig:
    """Load and validate a YAML config file."""
    with Path(path).open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    if not isinstance(raw, dict):
        raise ValueError(f"Config file {path} must contain a mapping at top level")
    return AppConfig.model_validate(raw)
