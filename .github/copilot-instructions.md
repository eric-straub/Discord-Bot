<!-- GitHub Copilot / AI agent instructions for the Discord-Bot repo -->
# Copilot Instructions — Discord-Bot

These notes capture project-specific patterns and developer workflows so an AI coding agent can be immediately productive.

1. Project overview
- **What it is:** A single-process Discord bot using discord.py. Entrypoint is `bot.py` which creates `MyBot`, loads cogs, and calls `bot.run(TOKEN)`.
- **Major components:**
  - `bot.py` — bot lifecycle, intents, and cog loading (`setup_hook`).
  - `cogs/` — individual feature modules (each exports a Cog class and an `async def setup(bot)` that calls `bot.add_cog(...)`).
  - `data/` — runtime JSON storage (ranks, economy, settings). Files may be created on first use.
  - `validate_bot.py` — pre-flight checks useful to run before launching or when modifying runtime/config.

2. How to run & common dev commands
- Install dependencies: `python3 -m pip install -r requirements.txt`.
- Validate the project: `python3 validate_bot.py` (checks `.env`, syntax, dependencies, and JSON files).
- Run the bot locally: ensure `.env` contains `DISCORD_TOKEN` and `APPLICATION_ID`, then `python3 bot.py`.
- Debugging: logging is configured in `bot.py` with `logging.basicConfig(level=logging.DEBUG)` and `MyBot.on_error` prints tracebacks.

3. Cog / command patterns (concrete examples)
- Cogs live in `cogs/*.py`. Each file defines a `class X(commands.Cog)` and exposes `async def setup(bot): await bot.add_cog(X(bot))` (see `cogs/info.py`).
- Slash commands use `@app_commands.command(...)` and expect an `interaction: discord.Interaction` parameter. Example: `@app_commands.command(name="userinfo") async def userinfo(self, interaction, member: discord.Member = None):`.
- When adding a new cog, also add `await self.load_extension("cogs.yourcog")` to `MyBot.setup_hook()` in `bot.py` so it loads on startup.

4. Data & configuration conventions
- `.env` is used for secrets (`DISCORD_TOKEN`, `APPLICATION_ID`). The repo's validator expects `.env` to exist and to be in `.gitignore`.
- Persistent runtime data is stored as JSON under `data/` (e.g. `data/ranks.json`). `validate_bot.py` treats missing data files as acceptable (created on first use) but flags invalid JSON.

5. Code style and common gotchas
- Use `discord.py` idioms: prefer `app_commands` for slash commands, and `commands.Cog` for modular features.
- Use `interaction.response.send_message(...)` for replies in slash commands (not `ctx.send`). Many cogs reuse helper logic by calling other command methods (see `Info.whois` which calls `self.userinfo`).
- The built-in help command is disabled in `bot.py` (`help_command=None`). Don't re-enable it unless you intend to replace custom help features.

6. Adding features safely
- Before running changes locally, run `python3 -m py_compile bot.py` and `python3 -m py_compile cogs/yourcog.py` (the validator automates this).
- Run `python3 validate_bot.py` after adding new cogs or data keys — it will surface missing `.env` variables, syntax errors, and JSON problems.

7. Files to inspect when debugging specific concerns
- Startup / command registration: `bot.py` (look at `setup_hook` and `on_ready` where `bot.tree.sync()` runs).
- Cog behavior and Discord API usage: `cogs/*.py` (notably `cogs/info.py`, `cogs/welcome.py`, `cogs/rank.py`).
- Persistent storage: `data/*.json` and code paths that read/write them (search for `open("data/` to locate usages).

```markdown
# Copilot Instructions — Discord-Bot

These concise notes give an AI coding agent the repo-specific context needed to be productive quickly.

1) Big picture
- Single-process Discord bot using `discord.py` / `discord.ext.commands`.
- Entrypoint: `bot.py` — defines `MyBot`, configures `intents`, logging, `setup_hook`, and calls `bot.run(TOKEN)`.
- Feature modules: `cogs/*.py` — each cog exposes `async def setup(bot)` and registers a `commands.Cog`.
- Runtime storage: `data/*.json` (ranks, economy, settings). Files are created on first use; validator flags invalid JSON.

2) How the bot starts / loads code
- `MyBot.setup_hook()` explicitly calls `await self.load_extension("cogs.<name>")` for each cog (see `bot.py`).
- On `on_ready` the bot runs `await bot.tree.sync()` to register slash commands.

3) Developer workflows & commands (concrete)
- Install deps: `python3 -m pip install -r requirements.txt`
- Validate repo before running: `python3 validate_bot.py` (checks `.env`, files, syntax, dependencies, JSON validity).
- Run locally: ensure `.env` contains `DISCORD_TOKEN` and `APPLICATION_ID`, then `python3 bot.py`.

4) Cog / command conventions (examples)
- Use `@app_commands.command(...)` for slash commands that receive an `interaction: discord.Interaction`.
- Reply with `await interaction.response.send_message(...)` (this project prefers interaction responses over `ctx.send`).
- Each cog file ends with an `async def setup(bot): await bot.add_cog(MyCog(bot))` (see `cogs/info.py`).
- When adding a new cog, add `await self.load_extension("cogs.<yourcog>")` to `MyBot.setup_hook()` in `bot.py`.

5) Data, secrets & git rules
- Secrets: use `.env` for `DISCORD_TOKEN` and `APPLICATION_ID`. `validate_bot.py` expects `.env` to exist; `.gitignore` should include `.env` and `data/`.
- Persistent data lives under `data/` (e.g., `data/ranks.json`, `data/economy.json`). The validator treats absent files as OK but flags invalid JSON.

6) Tests, linting & quick checks
- Syntax checks are done with `python3 -m py_compile <file>`; `validate_bot.py` runs these for `bot.py` and each cog.
- The validator also checks for installed packages (`discord`, `dotenv`) and basic project structure.

7) Common gotchas & patterns to preserve
- Logging is set to `DEBUG` in `bot.py`; many debug prints are used (e.g., `on_socket_response`) — avoid removing them unless replacing with equivalent logging.
- The built-in help command is disabled (`help_command=None`) — do not re-enable without a replacement.
- Many commands reuse internal helper calls (e.g., `Info.whois` calls `self.userinfo`) — prefer reuse over duplication.

8) Files to inspect for specific tasks
- Startup, intent and cog loading: `bot.py`
- Pre-flight checks: `validate_bot.py`
- Examples of slash-commands, embeds, and interaction patterns: `cogs/info.py`, `cogs/welcome.py`, `cogs/rank.py`
- Persistent structures / sample JSON: `data/` (open `data/ranks.json` for the format used)

9) Short checklist for adding a new cog
- Create `cogs/yourcog.py` with a `commands.Cog` subclass and `async def setup(bot)` that adds the cog.
- Add `await self.load_extension("cogs.yourcog")` to `MyBot.setup_hook()` in `bot.py`.
- Run `python3 -m py_compile cogs/yourcog.py` then `python3 validate_bot.py`.
- Provide example usages in `TESTING.md` or README if behavior is non-obvious.

If you'd like, I can expand the storage format examples (show `data/ranks.json` layout), add a step-by-step PR checklist, or include more code snippets from `cogs/*` for common idioms.
```
