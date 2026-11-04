# Muntar el servidor a Hetzner

Guia pas a pas per crear el servidor on correrà KronosTrading. El servidor **no té cap clau amb permisos per operar**: només descarrega dades, calcula senyals i envia avisos.

## 1. Crear el servidor (Hetzner Cloud Console)

1. Crea un projecte nou, per exemple `kronostrading`.
2. **Add Server**:
   - **Ubicació:** UE (Falkenstein, Nuremberg o Helsinki).
   - **Imatge:** Ubuntu 24.04.
   - **Tipus:** x86 amb **4 vCPU i 8 GB de RAM** o més (vCPU compartida). Els noms de les gammes canvien sovint; tria l'equivalent actual. Per als senyals diaris amb Kronos-small n'hi ha prou. Els backtests pesats es faran en una GPU llogada per hores.
   - **SSH key:** afegeix la teva clau pública. Si no en tens, crea-la al teu ordinador amb `ssh-keygen -t ed25519`.
   - **Cloud config:** enganxa-hi [`cloud-init.yaml`](cloud-init.yaml) **després d'haver posat la teva clau pública** a `ssh_authorized_keys`.
   - **Backups:** recomanat (té un cost addicional petit).
3. **Firewalls** (a la consola): regla d'entrada només per al port TCP 22 i, si pots, limitada a la teva IP. És una segona capa sobre `ufw`.

## 2. Primera connexió

```bash
ssh kronos@IP_DEL_SERVIDOR
```

Comprova que cloud-init ha acabat:

```bash
cloud-init status --wait
```

## 3. Accés al repositori (si és privat)

Crea al servidor una *deploy key* de només lectura:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N "" -C "kronos-hetzner"
```

```bash
cat ~/.ssh/github_deploy.pub
```

A GitHub, ves a **Settings → Deploy keys → Add deploy key**, enganxa-hi la clau i **no** marquis "Allow write access". Després:

```bash
printf 'Host github.com\n  IdentityFile ~/.ssh/github_deploy\n  IdentitiesOnly yes\n' >> ~/.ssh/config
```

## 4. Instal·lar el projecte

```bash
git clone --recurse-submodules git@github.com:pinxaolives/KronosTrading.git ~/KronosTrading
```

```bash
bash ~/KronosTrading/deploy/hetzner/setup.sh
```

L'script instal·la Python 3.11 amb `uv` i les dependències (torch de CPU), crea `.env` a partir de `.env.example` (amb permisos 600) i passa `make check` i `kt config-check`.

## 5. Secrets

Edita `~/KronosTrading/.env` al servidor (mai al repositori):

- `KT_TELEGRAM_BOT_TOKEN` i `KT_TELEGRAM_CHAT_ID`: fase 3.
- `KT_FRED_API_KEY`: dades macro, gratuïta.
- `KT_EODHD_API_KEY`: opcional, només si Yahoo bloqueja la IP del servidor.

## 6. Què ve després

- **Fase 1:** comprovar que el servidor arriba a Hugging Face (pesos de Kronos) i a Yahoo/Stooq (dades), i generar el primer gràfic de previsió.
- **Fase 3:** un temporitzador de `systemd` executarà el treball diari després del tancament de cada mercat.
