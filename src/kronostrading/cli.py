"""Command-line entry point (`kt`). Phase commands are added as each phase lands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from kronostrading import __version__
from kronostrading.config import Secrets, load_config
from kronostrading.logs import configure_logging, get_logger

app = typer.Typer(no_args_is_help=True, help="KronosTrading — signals only, no order execution.")


@app.callback()
def _main(log_level: Annotated[str, typer.Option(help="Log level")] = "INFO") -> None:
    configure_logging(log_level)


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)


@app.command("config-check")
def config_check(
    config: Annotated[
        Path | None, typer.Option(help="YAML config path (default: KT_CONFIG_PATH)")
    ] = None,
) -> None:
    """Validate the configuration and list warnings (e.g. unverified broker fees)."""
    log = get_logger("config")
    secrets = Secrets()
    path = config or secrets.config_path
    cfg = load_config(path)
    log.info(
        "config_ok",
        path=str(path),
        instruments=[i.id for i in cfg.enabled_instruments],
        model=cfg.kronos.model_id,
        capital=cfg.account.capital,
        risk_per_trade=cfg.risk.risk_per_trade,
    )
    for w in cfg.warnings():
        log.warning("config_warning", detail=w)
    log.info(
        "secrets_present",
        telegram=secrets.telegram_bot_token is not None,
        fred=secrets.fred_api_key is not None,
        eodhd=secrets.eodhd_api_key is not None,
    )


if __name__ == "__main__":
    app()
