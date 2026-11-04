# KronosTrading

Sistema d'**avisos de swing trading** (espelmes diàries) per a ETF, ETC i accions de baixa volatilitat, basat en previsions del model [Kronos](https://github.com/shiyu-coder/Kronos). **No executa ordres:** proposa operacions amb entrada, stop, objectiu i mida, i tu decideixes si les executes.

> ⚠️ Cap model garanteix beneficis. La majoria d'estratègies que surten bé al backtest no aguanten en real. Aquest sistema prioritza mesurar honestament per sobre de prometre resultats.

## Estat

| Fase | Contingut | Estat |
|---|---|---|
| 0 | Esquelet, configuració i servidor Hetzner | ✅ |
| 1 | Dades, wrapper de Kronos, gràfic de previsió | ⏳ |
| 2 | Backtest walk-forward i informe | — |
| 3 | Risc, cartera ombra, diari, Telegram, treball diari | — |
| 4 | Fine-tuning (opcional) | — |

## Instal·lació

Requereix Python 3.11 i [uv](https://docs.astral.sh/uv/).

```bash
git clone --recurse-submodules git@github.com:pinxaolives/KronosTrading.git
```

```bash
make setup          # core + dev, without torch
```

```bash
make setup-kronos   # adds torch (CPU) + Kronos dependencies
```

```bash
cp .env.example .env && make check && make config-check
```

Per al servidor, vegeu [`deploy/hetzner/README.md`](deploy/hetzner/README.md). L'arquitectura és a [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Configuració

Tot és a `config/default.yaml`: instruments (ETF i ETC configurables), capital, risc, perfils de comissions de cada broker, paràmetres de Kronos i dels senyals. Els secrets van a `.env`.

**Les comissions de broker són provisionals** (`verified: false`) fins que les comprovis; `kt config-check` t'ho recordarà.

## Limitacions conegudes

- Kronos no es pot instal·lar amb pip; s'inclou com a submòdul fixat a un commit concret.
- No se sap fins a quina data arriben les dades de preentrenament de Kronos, de manera que els backtests anteriors a l'agost de 2025 poden ser optimistes.
- `yfinance` no és una API oficial i Yahoo pot bloquejar IP de centres de dades. Hi ha fonts alternatives previstes.
