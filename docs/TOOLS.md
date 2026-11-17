# Eines externes: decisions

> Principi: **construïm només el que no existeix** (la puntuació de Kronos, la mesura honesta del seu valor amb les teves condicions reals i el pla d'operació adaptat). La resta la cobreixen eines existents.
>
> Cap eina, ni totes juntes, aporta un avantatge demostrat fora de mostra i net de costos. Mesurar-lo és la feina d'aquest projecte, i la fase 1b decideix si n'hi ha.

## Fem servir

| Eina | Paper | Notes |
|---|---|---|
| **Kronos** | Nucli de la previsió | Validat al paper per a **rànquing transversal** (RankIC), no per al timing d'un sol actiu. Per això la fase 1b prova tots dos modes. No hi ha cap llindar fixat a dit (com el "70 de 100" que circula): els llindars surten del valor esperat i de la calibració mesurats en les finestres d'entrenament. |
| **TradingView** (pla gratuït) | Gràfics, revisió manual, indicador Pine que replica les regles tècniques, Strategy Tester com a auditoria independent del setup | El pla gratuït té molt poques alertes actives i no té webhooks. El canal principal d'avisos és Telegram. Les alertes de TV es reserven per als stops de les posicions obertes. |
| **justETF** | Triar els ETF i ETC UCITS de l'univers | Ús manual; el resultat va a `config/default.yaml`. |
| **FRED** | Sèries macro per al règim (tipus reals, crèdit, corba, divisa) | Gratuït amb clau. Sèries de mercat, que no es revisen. |
| **Yahoo (yfinance) / Stooq** | Preus diaris | Gratuïts. Yahoo pot bloquejar la IP del servidor; Stooq és l'alternativa. |
| **quantstats** | Mètriques i informe HTML | Evita escriure el mòdul d'informes des de zero. |
| **vectorbt** | Exploració ràpida de variants del setup | Només per explorar. La validació final es fa sempre amb el motor walk-forward propi. |
| **Portfolio Performance** | Cartera real en EUR i fiscalitat (FIFO) | Fora del sistema. |
| **Claude** | Resum de notícies o del document informatiu d'un candidat | Context per a l'usuari, no és un senyal. Opcional, a partir de la fase 3. |

## Agafem idees, no l'eina

| Eina | Què n'agafem |
|---|---|
| **freqtrade** | **Anàlisi de look-ahead** (el senyal a t no canvia si s'eliminen les dades posteriors a t) i **anàlisi recursiva** (el senyal no canvia segons quant històric es carregui abans de la finestra). Tots dos són tests obligatoris. El seu *dry-run* equival a la nostra cartera ombra. |
| **daily_stock_analysis** | Resum de notícies dels candidats al mòbil, fet amb una sola crida a un LLM. |

## Opcionals o aparcades

| Eina | Quan |
|---|---|
| **OpenBB** | Adaptador de `DataSource` si algun dia calen molts proveïdors. El seu servidor MCP pot servir per a la recerca manual amb Claude. |
| **Qlib** | Fase 4 (fine-tuning) o si passem a un univers gran d'accions. |
| **Chronos / TimesFM** | Models de contrast darrere la interfície `Forecaster`, per saber si l'especialització financera de Kronos aporta alguna cosa. |
| **Morningstar / Koyfin / TIKR** | Filtre fonamental trimestral d'accions, fet a mà. |
| **EODHD** | Font de pagament, només si Yahoo i Stooq fallen des del servidor. |

## Descartades

| Eina | Motiu |
|---|---|
| **RD-Agent** | Amb un univers petit, generar centenars de factors sobre la mateixa història és trobar casualitats. A més, executa codi generat per un LLM: mai al servidor de senyals. |
| **TradingAgents, ai-hedge-fund** | No són deterministes i el backtest queda contaminat pel tall de coneixement del LLM. |
| **ccxt, hummingbot** | Fora d'abast (cripto i market making). |
| **NautilusTrader** | Motor d'execució, i nosaltres no executem ordres. |
| **Serveis de senyals "amb IA"** | Opacs, no es poden validar. |
