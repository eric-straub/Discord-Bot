# Discord-Bot — AI Coding Guidelines

This repository is a small, modular Discord bot that uses `discord.py` and the Cog pattern. The bot loads cogs explicitly in `bot.py` and stores runtime data in `data/*.json` files.

**Big Picture**
- Bot entrypoint: `bot.py` — creates `MyBot`, sets `intents`, and loads cogs in `MyBot.setup_hook()`.
- Command types: slash commands via `@app_commands.command()` and legacy prefix commands via `@commands.command()`.
- Persistent runtime data lives in `data/` (e.g., `ranks.json`). Cogs read/write these files directly.

**Key Files / Directories**
- `bot.py`: application_id (env), cog loading (`await self.load_extension("cogs.NAME")`), `on_ready()` syncs `bot.tree`.
- `cogs/`: place new cogs here. Each module exposes `async def setup(bot)` that registers the cog.
-- `data/`: JSON backing storage. `ranks.json` maps user_id → `{xp, level}`.
- `requirements.txt`: runtime deps (install with `pip install -r requirements.txt`).

How to run locally
- Create `.env` with `DISCORD_TOKEN=...` (and optional `APPLICATION_ID`).
- Install deps: `pip install -r requirements.txt`.
- Run: `python bot.py` (or `python3 bot.py`). The repo contains `test.py` — run `python test.py` if you want quick checks.

Patterns and Conventions (project-specific)
- Cogs must expose `async def setup(bot)` that calls `await bot.add_cog(MyCog(bot))` (see `cogs/general.py`).
- Slash command handlers use `interaction.response.*` (immediate response) or `defer()`+`followup` when necessary (`cogs/general.py:test`).
- Prefix commands use `ctx` and `ctx.send()` (see `cogs/general.py:echo` and `ping_cmd`).
-- Event listeners inside cogs use `@commands.Cog.listener()` (e.g., `on_message` in `rank.py`, `on_interaction` in `general.py`).
-- Data files are written synchronously with `json.dump(..., indent=4)` — small size expected; keep writes concise and avoid long blocking operations inside command handlers.

Data shape examples
- `data/ranks.json`:
    - map user_id → `{ "xp": <int>, "level": <int> }`

Debugging & developer workflows
- Logging: `logging.basicConfig(level=logging.DEBUG)` is enabled in `bot.py` for development.
- Gateway logging: `on_socket_response` prints select events to help debug slash delivery.
- Add a new cog: create `cogs/your_cog.py` with a Cog class and `async def setup(bot)`; then add `await self.load_extension("cogs.your_cog")` in `MyBot.setup_hook()` in `bot.py`.

Small implementation notes for AI agents
- Prefer editing existing cogs without renaming public symbols; follow existing style (spaces, small helper functions like `load_ranks()`/`save_ranks()`).
- When changing data formats, update both reader/writer helpers in the cog and any consumers (e.g., `rank.py` & `parry.py`).
- Keep bot startup deterministic: preserve `await bot.tree.sync()` in `on_ready()` unless changing command registration strategy.

If anything here is unclear or you want more examples (e.g., adding a new slash command or unit-testing a cog), tell me which section to expand.
