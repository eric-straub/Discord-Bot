**Repository Overview**

A Discord bot built with `discord.py` using Cog-based architecture. Dual command support (slash + prefix), JSON-backed persistence in `data/`, and pre-flight validation. Key files:

- `bot.py` : Entry point; configures `Intents`, creates `MyBot`, loads cogs in `setup_hook`, runs bot. Implements `on_member_join` for autorole and `on_socket_response` for gateway event logging.
- `validate_bot.py` : Pre-flight validator — checks `.env` vars, file structure, cog syntax via `python -m py_compile`, dependency installation, and JSON integrity. Run before deployment.
- `utils.py` : Shared utilities; `is_admin(user_id)` checks against `ADMIN_IDS` env var (comma-separated Discord user IDs).
- `cogs/*.py` : Feature modules (Cog subclasses). Each provides `async def setup(bot)` for registration via `await bot.add_cog(...)`.

**Architecture & Flows**

- **Cog modularity**: Each `cogs/*.py` file implements a `commands.Cog` subclass with slash/prefix commands. Loaded in `bot.setup_hook()` via `await self.load_extension("cogs.cog_name")`.
- **Command patterns**: Slash commands use `@app_commands.command` with `interaction.response.*` / `interaction.followup.*`. Prefix commands use `@commands.command` with `ctx`. For operations >3s, always `await interaction.response.defer()` first.
- **JSON persistence**: Files in `data/` are lazily created by cogs. Pattern: `load with fallback → modify dict → save immediately`. User/Guild IDs stored as strings. `validate_bot.py` warns about missing files (auto-created on use) but fails on malformed JSON.
- **Cross-cog communication**: Access via `self.bot.get_cog('CogClassName')` then call methods directly. Examples:
  - `trivia.py` → `RankSystem.award_xp(user_id, amount)` and `Economy._add_balance(user_id, amount)`
  - `casino.py` → `Economy._add_balance()` / `Economy._subtract_balance()` for betting
  - Pattern: `cog = self.bot.get_cog('CogName')` → `if cog:` → `await cog.method()` (or sync `cog.method()`)
- **Event listeners**: Use `@commands.Cog.listener()` for Discord events (`on_message` in `rank.py` for XP gain). `bot.py` handles `on_member_join` for autorole.
- **Gateway logging**: `bot.py` logs key events (`INTERACTION_CREATE`, `APPLICATION_COMMAND_CREATE`, `READY`) via `on_socket_response()` for debugging. Uses print statements, not logging framework.

**Developer Workflows**

1. **Pre-flight validation**: `python3 validate_bot.py` before starting bot. Checks: `.env` vars, file structure, cog syntax (`python -m py_compile`), dependencies, JSON integrity. Warns on missing data files (auto-created), fails on malformed JSON/missing env vars.
2. **Local development**: Create `.env` with `DISCORD_TOKEN`, `APPLICATION_ID`, `ADMIN_IDS` → run `python3 bot.py`.
3. **Slash command sync**: Automatic in `bot.on_ready()` via `await bot.tree.sync()`. No manual sync needed.
4. **Testing interactive features**: Requires live Discord server. Games (`games.py`) and casino (`casino.py`) use button controls that need real Discord environment.
5. **Syntax validation**: Run `python -m py_compile cogs/*.py` (done by validator). Use formatters like `black` if desired.

**Project Conventions**

- **Dual commands**: Provide slash + prefix parity when useful (see `general.py`: `/ping` and `!ping`). Prefer both unless slash-only.
- **Cog setup**: Include `async def setup(bot)` at bottom of cog files. Register bot state there (e.g., `bot.start_time = time.time()`). Load cogs in `bot.py`'s `setup_hook()`.
- **Error handling**: Local try/catch with print statements. Slash: `defer()` → work → `followup.send()` for long ops.
- **Data patterns**: `os.makedirs("data", exist_ok=True)` before write. Load with fallback → modify → save immediately. Example: `rank.py`.
- **IDs in JSON**: Always strings, never integers. E.g., `"123456789012345678"` for user/guild IDs.
- **Background tasks**: `self.bot.loop.create_task()` for async watchers (see `trivia.py`). Store task refs, cancel on cleanup.
- **Cooldowns**: `time.time()` comparisons in instance dicts. Pattern: `if now - last < cooldown: return` then `self.cooldowns[user_id] = now`. Example: `rank.py` 10s XP cooldown.
- **Admin checks**: `utils.is_admin(user_id)` for env-based perms. `interaction.user.guild_permissions.*` for server perms.
- **Interactive UI**: `discord.ui.View` with `discord.ui.Button` for games/menus. Pattern: subclass View → add buttons with callbacks → pass to `interaction.response.send_message(view=view)`. Set `timeout`, handle cleanup. Examples: `games.py` (Pong/Snake), `casino.py` (blackjack).
- **Trivia answers**: Spoiler tags `||answer||` prevent cheating. Extract via regex `r"\|\|(.+?)\|\|"`, normalize (lowercase, strip punctuation), fuzzy match with `difflib.SequenceMatcher` (0.78 threshold).

**Integration & Dependencies**

- Primary: `discord.py`. Secondary: `python-dotenv` for `.env` loading.
- `requirements.txt`: pinned packages. Match in CI/local envs.
- Required intents: `message_content`, `members`, `presences` (set in `bot.py`).

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
- `trivia` — interactive trivia questions with spoiler-based answers, fuzzy matching, XP/credit rewards
- `casino` — blackjack gambling game with betting mechanics
- `fun` — dice rolls (NdX format), coin flip, 8ball, rock-paper-scissors, random choice
- `games` — interactive games (Pong, Snake, Conway's Game of Life) with button controls and auto-updates

Data files (JSON in `data/`):
- `ranks.json` — `{"users": {"user_id": {"xp": int, "level": int}}, "xp_cooldowns": {"user_id": float}}` - Level formula: `floor(sqrt(xp / 50))`
- `economy.json` — `{"users": {"user_id": {"balance": int, "total_earned": int}}, "daily_cooldowns": {"user_id": float}}`

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
