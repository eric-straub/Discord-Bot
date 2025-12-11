# Validator (`validate_bot.py`)

`validate_bot.py` is a pre-flight script to detect common issues before launching the bot.

What it checks:

- `.env` existence and presence of `DISCORD_TOKEN` and `APPLICATION_ID`.
- Presence of required top-level files: `bot.py`, `requirements.txt`, `README.md`.
- Presence of expected cogs under `cogs/`.
- Python syntax checks for `bot.py` and all cogs using `python -m py_compile`.
- Installed dependencies: checks for `discord` and `dotenv` imports.
- `data/` directory existence and validity of JSON files (checks `data/ranks.json`, `data/economy.json`, `data/welcome.json`, `data/warns.json`, `data/settings.json`).
- `.gitignore` contains `.env` and `data/` entries.

How to run:

```bash
python3 validate_bot.py
```

Interpreting results:

- ✅ Lines indicate checks that passed.
- ❌ Errors must be fixed before running the bot (e.g., syntax errors, missing `.env`).
- ⚠️ Warnings indicate potential issues that may be acceptable but should be reviewed (e.g., missing optional data files).

If you add new data files or cogs, update `validate_bot.py` to include them in the checks so the validator remains useful.
