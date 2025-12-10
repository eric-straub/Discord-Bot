# Discord-Bot — AI Coding Guidelines
# Discord-Bot — AI Coding Guidelines

This repo is a small, modular Discord bot built on `discord.py`. The design centers on a single `bot.py` entrypoint, modular Cogs in `cogs/`, and small JSON-backed runtime state in `data/`.

**Big Picture**
- Entrypoint: `bot.py` — constructs `MyBot`, sets `intents`, loads cogs in `MyBot.setup_hook()`, and syncs slash commands in `on_ready()` (`await bot.tree.sync()`).
- Commands: mix of application (slash) commands (`@app_commands.command`) and legacy prefix commands (`@commands.command`).
- Persistent state: small JSON files under `data/` (examples: `ranks.json`, `welcome.json`). Cogs read/write them directly.

**Key Files / Patterns**
- `bot.py`: create/initialize `MyBot`, enable `message_content`/`members` intents, load cogs via `await self.load_extension("cogs.NAME")`, and keep `await bot.tree.sync()` in `on_ready()`.
- `cogs/`: each module exposes `async def setup(bot)` and registers the Cog via `await bot.add_cog(MyCog(bot))`.
- `cogs/rank.py`: XP system — `load_ranks()`/`save_ranks()` helpers, `calculate_level(xp)` (used in tests), and `on_message` listener awards XP with a 10s cooldown.
- `cogs/welcome.py`: per-guild welcome config persisted to `data/welcome.json`; includes `os.makedirs('data', exist_ok=True)` (good pattern to follow).
- `cogs/music.py`: uses `yt_dlp` and FFmpeg; requires `ffmpeg` binary on the host and `yt-dlp` in `requirements.txt`.
- `tests/test_rank.py`: small unit tests — run with `pytest`.

**How to run & test (developer workflows)**
- Environment: create `.env` with `DISCORD_TOKEN` and optional `APPLICATION_ID`.
- Install deps: `pip install -r requirements.txt` (project expects `discord.py`, `python-dotenv`, `yt-dlp`, etc.).
- Run bot locally: `python3 bot.py` — you should see "Slash commands synced." and "Bot is ready." on startup.
- Run tests: `pytest tests/test_rank.py` or `pytest -q` for all tests.

**Conventions & Implementation notes for AI agents**
- Cog shape: export `async def setup(bot)` and call `await bot.add_cog(...)` — follow existing naming and constructor style (pass `bot` into the Cog).
- Command handling: prefer `interaction.response.send_message(...)` for immediate replies; if doing heavy work, `await interaction.response.defer()` then use `interaction.followup.send(...)`.
- Event listeners: use `@commands.Cog.listener()`; do not raise from listeners — swallow/log errors (see `general.on_interaction` and `Welcome.on_member_join`).
- Data files: current code uses synchronous `json.dump(..., indent=4)`. Files are small, but always ensure `data/` exists (use `os.makedirs('data', exist_ok=True)` or `Path('data').mkdir(parents=True, exist_ok=True)`).
- Permissions: admin commands check `interaction.user.guild_permissions.manage_guild` — follow this pattern for admin-only operations.
- Logging & debugging: `logging.basicConfig(level=logging.DEBUG)` is enabled. `MyBot.on_socket_response` prints gateway events — avoid removing this while diagnosing slash delivery.

**Integration points & external dependencies**
- `music.py` relies on system `ffmpeg` and `yt-dlp` (Python package `yt_dlp`). Document both runtime and system-level deps when changing music functionality.
- Persistent files: `data/ranks.json`, `data/welcome.json` — keep keys stable when evolving formats; update all consumers when changing shapes.

**Testing & quick checks**
- Targeted test run: `pytest tests/test_rank.py::test_calculate_level_examples`.
- When changing `calculate_level` or rank persistence, update `tests/test_rank.py` accordingly.

**Examples to reference while editing**
- Add a new cog: mirror `cogs/general.py` + `async def setup(bot): await bot.add_cog(MyCog(bot))` and add `await self.load_extension('cogs.my_cog')` in `MyBot.setup_hook()`.
- XP calculation: see `cogs/rank.py::calculate_level(xp)` and persisted shape in `data/ranks.json`.

**AI-agent specific guidance**
- Preserve exposed public symbols (Cog class names, `setup` functions) unless intentionally refactoring across the codebase.
- When changing data formats, update both load/save helpers and every cog that reads them (search for `RANK_FILE` / `WELCOME_FILE`).
- Keep changes minimal and consistent with existing simple style (no large refactors without explicit instruction).

If anything here is unclear or you want the guidelines expanded (example PR flow, semantic versioning, or more test coverage), tell me which section to iterate on.
