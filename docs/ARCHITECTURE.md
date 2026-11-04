# Arquitectura de KronosTrading

> Estat: **proposta en revisió.** Les capes de context fonamental i macro (secció 3) estan pendents d'aprovació.

## 1. Objectiu

Sistema d'**avisos de swing trading** en espelmes diàries per a ETF i ETC (or, índexs) i accions de baixa volatilitat. **No executa ordres:** genera un pla d'operació (entrada, stop, objectiu, mida, R:R, probabilitat i valor esperat) i l'envia per Telegram. L'usuari executa a mà a TradingView, MyInvestor o Revolut.

**Paràmetres inicials:** capital orientatiu de 10.000 €, risc de 100 € per operació, només llarg, instruments configurables a `config/default.yaml`.

## 2. Mòduls

```
src/kronostrading/
├── config/      Pydantic + YAML; secrets via .env (KT_*)
├── data/        yfinance / stooq (/ eodhd) sources, Parquet cache, trading calendar (future timestamps)
├── models/      Kronos wrapper (multi-path via predict_batch), naive/drift/SMA baselines
├── context/     [proposed] macro regime (FRED), event calendar, fundamental screen
├── signals/     technical setups, Kronos scoring (P(TP before SL), EV in R), filters
├── backtest/    walk-forward engine (next-open fills, stop_mode close|intraday, gaps, min fees),
│                forecast store, calibration
├── risk/        sizing (fixed EUR risk, position cap), exits (SL/TP/time/trailing), limits
├── portfolio/   shadow portfolio (every signal), manual journal (your real positions)
├── alerts/      Telegram (chart PNG + TradingView link + /entrada /sortida), Slack
├── live/        daily job (systemd timer on Hetzner)
└── reports/     metrics, plots, HTML report
```

## 3. Flux de decisió en tres capes

| Capa | Freqüència | Funció | Entrades |
|---|---|---|---|
| **A. Univers** | Mensual | Quins actius són elegibles | Llista configurada d'ETF/ETC; accions: filtre de qualitat, liquiditat i baixa volatilitat |
| **B. Règim** | Setmanal o diària | Vent a favor o en contra; multiplicador de mida | Tendència de l'índex, sèries macro (FRED), calendari d'esdeveniments |
| **C. Setup i timing** | Diària | Candidat → puntuació → pla d'operació | Setup tècnic (tendència + retrocés), Kronos (camins múltiples), filtres de cost i volatilitat |

En el backtest es mesura la contribució de cada capa per separat: setup sol, setup + Kronos, Kronos sol, i amb o sense règim.

## 4. Regles metodològiques

- Decisió al tancament de t, execució a l'obertura de t+1. Test que "contamina" les dades posteriors a t.
- Walk-forward: ajust en la finestra d'entrenament i aplicació fora de mostra. Tram final reservat a partir del 2025-09 (posterior a la publicació de Kronos).
- Dades macro i fonamentals **point-in-time**, amb el retard de publicació aplicat. Si no hi ha historial point-in-time, la capa s'usa només en directe i no es reivindica cap resultat de backtest per a ella.
- Comparativa obligatòria: naive, SMA, buy & hold de l'actiu i de l'índex.
- Costos: perfils de broker amb comissió mínima, spread, slippage i canvi de divisa.

## 5. Infraestructura

VPS a Hetzner (CPU, Ubuntu 24.04) per a dades, senyals i avisos. GPU llogada per hores per precalcular les previsions històriques; els resultats es desen en Parquet i es pugen al VPS. Vegeu [`deploy/hetzner/README.md`](../deploy/hetzner/README.md).

## 6. Fets de Kronos que condicionen el disseny

Vegeu els detalls a `third_party/Kronos/model/kronos.py` (commit `67b630e`):

- `sample_count` fa la mitjana dels camins internament; per obtenir una distribució fem servir `predict_batch` amb la finestra repetida.
- Els timestamps futurs els ha de donar l'usuari, i per això cal un calendari de mercat.
- Context màxim de 512 per a small i base, i de 2048 per a mini. No hi ha KV-cache.
- Revisions de Hugging Face fixades a la configuració, i `.eval()` explícit.
- La data de tall de les dades de preentrenament és desconeguda: hi ha risc de fuita en els backtests anteriors a l'agost de 2025.
