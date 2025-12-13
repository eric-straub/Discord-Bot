# Copilot Instructions for Discord-Bot

## Project Overview
- This is a modular Discord bot using `discord.py` with cogs for features: moderation, economy, rank/xp, fun, info, trivia, welcome, and settings.
- Main entry: `bot.py` (loads all cogs in `cogs/` via `MyBot.setup_hook`).
- Persistent data is stored as JSON in `data/` (see `docs/data-format.md`).
- Environment variables (`.env`) are required: `DISCORD_TOKEN`, `APPLICATION_ID`.

## Key Workflows
- **Validation:** Always run `python3 validate_bot.py` before running or submitting changes. This checks for missing files, syntax errors, required env vars, and data validity.
- **Run Locally:**
  1. `python3 -m venv .venv && source .venv/bin/activate`
  2. `python3 -m pip install -r requirements.txt`
  3. Create `.env` with required tokens.
  4. `python3 validate_bot.py`
  5. `python3 bot.py`
- **Production:** Use a process manager (systemd, Docker) and secure env var management (see `docs/setup.md`).

## Code Structure & Patterns
- **Cogs:** Each feature is a cog in `cogs/` (see `docs/cogs.md`). Register new cogs in `MyBot.setup_hook()`.
- **Commands:** Use `@app_commands.command` for slash commands, `@commands.command` for prefix commands. Prefer slash commands for new features.
- **Data Files:** Each cog manages its own JSON file in `data/`. Handle missing/invalid files gracefully (auto-create or warn).
- **Settings:** Per-guild config is in `data/settings.json`, managed by the settings cog.
- **Validation:** If you add new cogs or data files, update `validate_bot.py` to include them in checks.

## Conventions & Practices
- Use type hints where helpful, but don't over-annotate.
- Avoid global mutable state outside of `data/` storage.
- Document new commands and data format changes in `docs/`.
- Use small, focused commits and branch from `dev`.
- If you add testable logic, include tests and document how to run them.

## Integration Points
- **discord.py**: All bot logic is built on top of `discord.py` (see `requirements.txt`).
- **dotenv**: Used for loading secrets from `.env`.
- **Data Migration:** If you change data formats, update `docs/data-format.md` and provide migration notes.

## Examples
- Adding a cog: see `docs/cogs.md` and register in `MyBot.setup_hook()`.
- Adding a data file: create in `data/`, document in `docs/data-format.md`, and update `validate_bot.py`.

## References
- See `docs/` for extended guides: `setup.md`, `cogs.md`, `data-format.md`, `validation.md`.
- See `CONTRIBUTING.md` for PR workflow and coding guidelines.

---

If you are unsure about a workflow or pattern, check the relevant `docs/` file or ask for clarification in your PR.
