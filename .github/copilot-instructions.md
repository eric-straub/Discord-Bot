# Discord Bot - AI Agent Instructions

A modular Discord bot built with `discord.py` using Cog-based architecture, JSON persistence, and dual command support (slash + prefix).

## Architecture Overview

**Core Files:**
- `bot.py` — Entry point. Configures `Intents`, creates `MyBot(commands.Bot)`, loads cogs via `setup_hook()`, and handles `on_member_join` (autorole) + `on_socket_response` (gateway logging for INTERACTION_CREATE/READY events)
- `validate_bot.py` — Pre-flight validator. Checks `.env` vars, file structure, cog syntax (`python -m py_compile`), dependencies, JSON integrity. **Always run before deployment**
- `utils.py` — Shared helpers. `is_admin(user_id)` checks against `ADMIN_IDS` env var (comma-separated Discord user IDs)
- `cogs/*.py` — Feature modules. Each is a `commands.Cog` subclass with `async def setup(bot)` for registration

**Cog Loading:** In `bot.py`'s `setup_hook()`, cogs are loaded via `await self.load_extension("cogs.cog_name")`. Active cogs: `general`, `rank`, `economy`, `trivia`, `casino`, `fun`, `games`.

**Bot Configuration:**
- **Version tracking:** `__version__` in `bot.py` (current: 0.0.3-alpha)
- **Logging:** `logging.basicConfig(level=logging.INFO)` — use INFO for prod, DEBUG for dev
- **Help command disabled:** `help_command=None` in bot init to avoid conflicts with custom help

**Command Patterns:**
- **Slash commands:** `@app_commands.command` + `interaction.response.send_message()` / `interaction.followup.send()`
- **Prefix commands:** `@commands.command` + `ctx.send()`
- **Deferral rule:** For operations >3s, **always** `await interaction.response.defer()` first (see `casino.py` line 82, `trivia.py` line 102)
- **Dual support:** Implement both slash + prefix where useful (e.g., `general.py`: `/ping` and `!ping`)
- **Slash sync:** Automatic on bot startup via `await bot.tree.sync()` in `on_ready()` (line 105)

## Data Persistence

**Pattern:** Load with fallback → modify dict → save immediately. Files in `data/` are auto-created on first use.

**Critical Rules:**
- **User/Guild IDs always strings:** `"123456789012345678"`, never integers
- **Auto-create data directory:** Use `os.makedirs("data", exist_ok=True)` before writes
- **Modern format includes cooldowns:** `{"users": {...}, "xp_cooldowns": {...}}` (see `rank.py` lines 12-34 for migration pattern)
- **Immediate persistence:** Save after every mutation to prevent data loss

**Example (see `rank.py` lines 12-34):**
```python
def load_ranks():
    if not os.path.exists(RANK_FILE):
        return {"users": {}, "xp_cooldowns": {}}
    with open(RANK_FILE, "r") as f:
        data = json.load(f)
        # Migrate old format if needed
        if "users" not in data:
            data = {"users": data, "xp_cooldowns": {}}
        return data

def save_ranks_with_cooldowns(ranks_data, cooldowns):
    data = {
        "users": ranks_data,
        "xp_cooldowns": {str(k): v for k, v in cooldowns.items()}
    }
    with open(RANK_FILE, "w") as f:
        json.dump(data, f, indent=4)
```

**Data Files:**
- `ranks.json` — XP/level system. Level formula: `floor(sqrt(xp / 50))`. XP gain: 15-25 per message with 10s cooldown
- `economy.json` — Balances, total earned, daily cooldowns (24h). Structure: `{"users": {user_id: {balance, total_earned}}, "daily_cooldowns": {user_id: timestamp}}`
- `settings.json` — Per-guild configs: `{guild_id: {prefix, xp_enabled, autorole_enabled, autorole_id, modlog_channel}}` (see `bot.py` lines 44-57 for autorole usage)

## Cross-Cog Communication

**Pattern:** `self.bot.get_cog('CogClassName')` → null check → call methods.

**Real Examples:**

1. **Trivia → RankSystem + Economy** (`trivia.py` lines 245-265):
```python
rank_cog = self.bot.get_cog('RankSystem')
econ_cog = self.bot.get_cog('Economy')

if rank_cog:
    new_level = await rank_cog.award_xp(message.author.id, awarded_xp)  # async
if econ_cog:
    econ_cog._add_balance(message.author.id, awarded_credits)  # sync
```

2. **Casino → Economy** (`casino.py` lines 98-106):
```python
econ_cog = self.bot.get_cog('Economy')
if not econ_cog:
    await interaction.followup.send("Economy system not available.", ephemeral=True)
    return

econ_cog._ensure_user(user_id)
user_balance = econ_cog.economy[str(user_id)]['balance']
if not econ_cog._remove_balance(user_id, bet):
    await interaction.followup.send("Failed to place bet.", ephemeral=True)
```

**Key Methods:**
- `RankSystem.award_xp(user_id, amount)` — async, returns new level or None
- `Economy._add_balance(user_id, amount)` — sync, updates balance + total_earned
- `Economy._remove_balance(user_id, amount)` — sync, returns bool (success/fail)

## Event Listeners & Background Tasks

**Event Listeners:** Use `@commands.Cog.listener()` for Discord events.

**Example:** `rank.py` lines 70-92 — `on_message` awards 15-25 XP per message with 10s per-user cooldown:
```python
@commands.Cog.listener()
async def on_message(self, message: discord.Message):
    if message.author.bot or not message.guild:
        return
    
    user_id = message.author.id
    now = time.time()
    last = self.cooldowns.get(user_id, 0)
    if now - last < 10:
        return
    
    self.cooldowns[user_id] = now
    xp_gain = random.randint(15, 25)
    new_level = await self.award_xp(user_id, xp_gain)
    if new_level:
        await message.channel.send(f"🎉 **{message.author.mention} leveled up to Level {new_level}!**")
```

**Background Tasks:** `self.bot.loop.create_task()` for async watchers. Store task refs for cleanup.

**Example:** `trivia.py` lines 158-162 — time-bound trivia watcher:
```python
async def watcher():
    try:
        remaining = trivia['ends_at'] - time.time()
        if remaining > 0:
            await asyncio.sleep(remaining)
        if channel.id in self.active_trivia:
            await self._end_trivia(channel.id, reason="time")
    except asyncio.CancelledError:
        return

task = self.bot.loop.create_task(watcher())
trivia['task'] = task  # Store for cancellation
```

## Interactive UI (Buttons & Views)

**Pattern:** Subclass `discord.ui.View`, add buttons with callbacks, pass to `interaction.response.send_message(view=view)`. Set `timeout`.

**Example:** `casino.py` defines `BlackjackView` with Hit/Stand buttons. Used at line 173:
```python
view = BlackjackView(self, interaction.user)
await interaction.followup.send(embed=embed, view=view)
```

**Advanced Games:** `games.py` implements Pong and Snake with auto-update loops using `asyncio.sleep()` in button callbacks. Game state stored in `self.active_games[user_id]`.

See `games.py` for more complex examples with real-time rendering.

## Development Workflow

1. **Pre-flight check:** `python3 validate_bot.py` — checks env vars, syntax, deps, JSON integrity
   - Validates `.env` contains `DISCORD_TOKEN`, `APPLICATION_ID`, `ADMIN_IDS` (optional)
   - Checks file structure: `bot.py`, `requirements.txt`, `README.md`, `cogs/` directory
   - Compiles all cogs with `python -m py_compile` to catch syntax errors
   - Validates JSON files in `data/` for proper formatting
   - Checks dependencies from `requirements.txt` are installed
2. **Local run:** Create `.env` with `DISCORD_TOKEN`, `APPLICATION_ID`, `ADMIN_IDS` → `python3 bot.py`
3. **Slash command sync:** Automatic in `bot.on_ready()` via `await bot.tree.sync()`
4. **Testing:** Interactive features (games, casino) require live Discord server
5. **Error debugging:** Check `on_socket_response()` logs for INTERACTION_CREATE events

## Trivia System Special Patterns

**Dual Creation Methods:**
1. **Message mention:** Post message with "Category:" keyword to trigger `_handle_trivia_mention()` (lines 79-168)
2. **Slash command:** Use `/trivia_post` with explicit parameters

**DM Flow:** If message lacks spoiler `||answer||`, bot DMs user via `pending_trivia` dict (lines 107-126), user replies in DM, then trivia posts automatically (lines 212-306).

**Answer Matching:** 
- Extract from spoilers via `_extract_spoilers()` using regex `r"\|\|(.+?)\|\|"`
- Normalize with `_normalize_text()` to lowercase alphanumeric
- Fuzzy match with `difflib.SequenceMatcher` (0.78 threshold) - see lines 36-52
- Supports multiple accepted answers separated by `|` or `,`

**Multi-Winner Support:** `correct_users` list allows multiple users to answer (lines 482-510). First correct gets checkmark + rewards, subsequent get silent checkmark. Asker cannot answer their own trivia.

**Time-Bound Watcher:** Background task (`bot.loop.create_task()`) waits until `ends_at` timestamp (6am next day), then auto-ends trivia. Stored in `trivia['task']` for cancellation (lines 158-162, 291-299).

**Cancel Logic:** Only trivia asker or users with `manage_guild` permission can cancel active trivia.

## Project Conventions

- **Cog scaffold:** Every cog needs `async def setup(bot)` at bottom
- **Error handling:** Local try/catch with print statements. No logging framework beyond basicConfig
- **Cooldowns:** Manual `time.time()` comparisons in instance dicts (see `rank.py` line 84, `economy.py` daily cooldowns)
- **Admin checks:** `utils.is_admin(user_id)` for env-based perms; `interaction.user.guild_permissions.*` for server perms
- **Gateway logging:** `on_socket_response()` logs INTERACTION_CREATE/READY events for debugging (see `bot.py` lines 60-71)
- **Environment vars:** Always load with `python-dotenv` and provide defaults where sensible (e.g., `ADMIN_IDS` defaults to empty string)

## Key Examples to Reference

- **Command patterns:** `cogs/general.py` (dual slash/prefix), `cogs/rank.py` (event listener)
- **Cross-cog integration:** `cogs/trivia.py` lines 245-265, `cogs/casino.py` lines 98-106
- **Background tasks:** `cogs/trivia.py` lines 158-162 (async watcher)
- **Data persistence:** `cogs/rank.py` lines 12-34 (load/save pattern with migration)
- **Interactive UI:** `cogs/games.py` (Pong/Snake with auto-update), `cogs/casino.py` (blackjack buttons)
- **DM handling:** `cogs/trivia.py` lines 212-306 (pending trivia answer flow)

## Required Dependencies & Intents

- **Dependencies:** `discord.py`, `python-dotenv` (see `requirements.txt`)
- **Intents (bot.py lines 19-23):** `message_content`, `members`, `presences` — all required for XP tracking, autorole, and event listeners
- **Gateway Events:** `on_socket_response()` monitors INTERACTION_CREATE and READY for debugging
