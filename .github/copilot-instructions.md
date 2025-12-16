**Repository Overview**

This repository is a small Discord bot built with `discord.py` using a Cog-based design. The bot uses both slash (`@app_commands.command`) and prefix (`@commands.command`) commands and places runtime state and persistent data under the `data/` directory as JSON files (eg. `data/ranks.json`, `data/settings.json`). Key entry points and helpers:

- `bot.py` : Application entry; configures `Intents`, creates `MyBot`, loads cogs in `setup_hook`, and runs the bot. Also handles autorole assignment via `on_member_join_autorole()` event.
- `validate_bot.py` : Pre-flight validation script — run this before starting the bot to catch missing env vars, syntax errors, dependency issues, and data file problems.
- `utils.py` : Shared utilities; notably `is_admin(user_id)` which checks user IDs against the `ADMIN_IDS` env var (comma-separated list).
- `cogs/*.py` : Individual feature modules (cogs). Each cog exposes an `async def setup(bot)` factory which registers the cog via `await bot.add_cog(...)`.

**High-level architecture & flows**

- Cog-based modularity: each file in `cogs/` implements a `commands.Cog` subclass and provides both slash and/or prefix commands where needed. Cogs are registered by `bot.setup_hook()` in `bot.py`.
- Interaction flow: slash commands are implemented with `@app_commands.command` and respond via `interaction.response.*` or `interaction.followup.*`. Prefix commands use `@commands.command` and the standard `ctx` pattern.
- Persistent data: small JSON files under `data/` are lazily created/updated by cogs. `validate_bot.py` expects those files (or will note they will be created on first use).
- Cross-cog communication: Cogs access each other's functionality via `self.bot.get_cog('CogName')` and call public methods directly (example: `cogs/trivia.py` calls `RankSystem.award_xp()` and `Economy._add_balance()` to reward winners).

**Key developer workflows**

- Run pre-flight checks: `python3 validate_bot.py` — this checks `.env`, required files, cog syntax, and installed dependencies.
- Run the bot locally: create a `.env` with `DISCORD_TOKEN` and `APPLICATION_ID`, then `python3 bot.py`.
- Slash command sync: happens automatically in `bot.on_ready()` via `await bot.tree.sync()` — no manual sync needed during development.
- Linting / syntax: The repo relies on `python -m py_compile` checks in `validate_bot.py`; use your normal formatter (e.g. `black`) if desired but keep minimal diffs.

**Project-specific conventions**

- Dual command style: Provide parity between slash and prefix commands when useful (see `cogs/general.py` where `/ping` and `!ping` both exist). If adding commands, prefer providing both unless the feature is slash-only.
- Cog setup: Always include an `async def setup(bot)` at the bottom of new cog files and register any bot-level state there (examples: `bot.start_time = time.time()`).
- Error handling: handlers often catch exceptions locally and print for visibility, and slash handlers sometimes `defer()` then `followup.send()` when immediate responses fail. Follow this pattern for resilient interactive handlers.
- Data handling: read/write JSON in `data/` using simple `json.load`/`json.dump` patterns. The validator accepts missing data files (they are created on first use) but flags malformed JSON.
- User IDs in JSON: always store Discord user IDs as strings (e.g., `"89161521543811072"`), not integers, for JSON compatibility.
- Background tasks: use `self.bot.loop.create_task()` for async watchers (see `cogs/trivia.py` for timer-based game logic); always store task references and cancel them on cleanup.
- Cooldowns: implement per-user cooldowns with `time.time()` comparisons stored in instance dicts (see `cogs/rank.py` XP cooldown — 10 seconds between awards).
- Admin permissions: use `utils.is_admin(user_id)` to check if a user is in the `ADMIN_IDS` env var list. For server-specific perms, check `interaction.user.guild_permissions.*` (example: `manage_guild` in `cogs/trivia.py`).
- Trivia answer pattern: `cogs/trivia.py` uses spoiler tags (`||answer||`) to hide user answers and prevent cheating. Answers are extracted via regex, normalized (lowercased, punctuation removed), and matched with fuzzy string matching (difflib SequenceMatcher with 0.78 threshold).

**Integration & dependencies**

- Primary runtime dependency: `discord.py` (imported as `discord`). Secondary: `python-dotenv` to load `.env`.
- `requirements.txt` lists pinned packages for the environment; match those when running in CI or locally.
- Intents required: `message_content`, `members`, `presences` (set in `bot.py`).

**When editing or adding Cogs**

Example minimal cog scaffold to follow existing project style:

```python
import discord
from discord.ext import commands
from discord import app_commands

class ExampleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="hello", description="Say hello")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello!")

async def setup(bot):
    await bot.add_cog(ExampleCog(bot))
```

Follow these rules when changing code:
- Register the cog module name in `bot.setup_hook()` if it should load by default.
- Keep heavy I/O and blocking work off the event loop (use `asyncio.to_thread` or background tasks if needed).
- Use the existing lightweight logging/print patterns rather than introducing heavy logging frameworks without consensus.
- When cogs need to communicate, define clear public methods (prefixed without underscore) or protected helpers (prefixed with `_` for internal use only).

**Available Cogs & Data Files**

Current cogs in production (loaded by `bot.setup_hook()`):
- `general` — ping, hello, server stats, help command
- `rank` — XP/level system with message-based XP gain (15-25 XP per message, 10s cooldown), leaderboard
- `economy` — currency system with daily rewards (100 credits, 24h cooldown), balance checks, transfers
- `moderation` — warnings system, kick, ban, timeout, message purge
- `settings` — per-guild configuration (prefix, XP toggle, autorole, modlog channel)
- `trivia` — interactive trivia questions with spoiler-based answers, fuzzy matching, XP/credit rewards
- `casino` — blackjack gambling game with betting mechanics
- `fun` — dice rolls (NdX format), coin flip, 8ball, rock-paper-scissors, random choice

Data files (JSON in `data/`):
- `ranks.json` — `{"user_id": {"xp": int, "level": int}}` - Level formula: `floor(sqrt(xp / 50))`
- `economy.json` — `{"user_id": {"balance": int, "total_earned": int}}`
- `settings.json` — `{"guild_id": {"prefix": str, "xp_enabled": bool, "modlog_channel": int|null, "autorole_enabled": bool, "autorole_id": int|null}}`
- `warns.json` — `{"guild_id": {"user_id": [{"reason": str, "issued_by": str, "timestamp": str (ISO 8601)}]}}`

Note: All files are auto-created on first use. User and guild IDs are always stored as strings.

**Files & places to check for examples**

- Command patterns: `cogs/general.py`, `cogs/rank.py`
- Cross-cog integration: `cogs/trivia.py` (calls RankSystem and Economy)
- Background tasks & timers: `cogs/trivia.py` (async watcher pattern)
- Event listeners: `cogs/rank.py` (`on_message` for XP gain)
- Setup & lifecycle: `bot.py` and `cogs/*` `setup` functions
- Pre-run checks: `validate_bot.py`
- Data formats & docs: `data/` and `docs/*.md` (see `docs/data-format.md`)

If anything here is unclear or you'd like more examples (e.g., error-handling conventions, preferred JSON schema for `data/ranks.json`, or CI/run commands), tell me which area to expand and I will iterate.
