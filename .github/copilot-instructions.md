# Discord Bot - AI Agent Instructions

A modular Discord bot built with `discord.py` using Cog-based architecture, JSON persistence, and dual command support (slash + prefix).

## Architecture Overview

**Core Files:**
- `bot.py` — Entry point. Configures `Intents`, creates `MyBot(commands.Bot)`, loads cogs via `setup_hook()`, and handles `on_member_join` (autorole) + `on_socket_response` (gateway logging)
- `validate_bot.py` — Pre-flight validator. Checks `.env` vars, file structure, cog syntax (`python -m py_compile`), dependencies, JSON integrity. **Run before deployment**
- `utils.py` — Shared helpers. `is_admin(user_id)` checks against `ADMIN_IDS` env var (comma-separated Discord user IDs)
- `cogs/*.py` — Feature modules. Each is a `commands.Cog` subclass with `async def setup(bot)` for registration

**Cog Loading:** In `bot.py`'s `setup_hook()`, cogs are loaded via `await self.load_extension("cogs.cog_name")`. Active cogs: `general`, `rank`, `economy`, `trivia`, `casino`, `fun`, `games`.

**Command Patterns:**
- Slash commands: `@app_commands.command` + `interaction.response.send_message()` / `interaction.followup.send()`
- Prefix commands: `@commands.command` + `ctx.send()`
- For operations >3s, **always** `await interaction.response.defer()` first (see `casino.py` line 82, `trivia.py` line 102)
- Dual support where useful (e.g., `general.py`: `/ping` and `!ping`)

## Data Persistence

**Pattern:** Load with fallback → modify dict → save immediately. Files in `data/` are auto-created on first use.

**Critical Rules:**
- User/Guild IDs **always** stored as strings: `"123456789012345678"`, never integers
- Use `os.makedirs("data", exist_ok=True)` before writes
- New format includes cooldowns: `{"users": {...}, "xp_cooldowns": {...}}`

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
- `ranks.json` — XP/level system. Level formula: `floor(sqrt(xp / 50))`
- `economy.json` — Balances, total earned, daily cooldowns (24h)

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

See `games.py` for more complex examples (Pong, Snake) with auto-update loops.

## Development Workflow

1. **Pre-flight check:** `python3 validate_bot.py` — checks env vars, syntax, deps, JSON integrity
2. **Local run:** Create `.env` with `DISCORD_TOKEN`, `APPLICATION_ID`, `ADMIN_IDS` → `python3 bot.py`
3. **Slash command sync:** Automatic in `bot.on_ready()` via `await bot.tree.sync()`
4. **Testing:** Interactive features (games, casino) require live Discord server

## Project Conventions

- **Cog scaffold:** Every cog needs `async def setup(bot)` at bottom
- **Error handling:** Local try/catch with print statements. No logging framework
- **Cooldowns:** Manual `time.time()` comparisons in instance dicts (see `rank.py` line 84)
- **Admin checks:** `utils.is_admin(user_id)` for env-based perms; `interaction.user.guild_permissions.*` for server perms
- **Trivia answers:** Spoiler tags `||answer||` prevent cheating. Extract via `r"\|\|(.+?)\|\|"`, normalize, fuzzy match with `difflib.SequenceMatcher` (0.78 threshold) — see `trivia.py` lines 36-52

## Key Examples to Reference

- **Command patterns:** `cogs/general.py` (dual slash/prefix), `cogs/rank.py` (event listener)
- **Cross-cog integration:** `cogs/trivia.py` lines 245-265, `cogs/casino.py` lines 98-106
- **Background tasks:** `cogs/trivia.py` lines 158-162 (async watcher)
- **Data persistence:** `cogs/rank.py` lines 12-34 (load/save pattern)
- **Interactive UI:** `cogs/games.py` (Pong/Snake), `cogs/casino.py` (blackjack buttons)

## Required Dependencies & Intents

- **Dependencies:** `discord.py`, `python-dotenv` (see `requirements.txt`)
- **Intents (bot.py lines 19-23):** `message_content`, `members`, `presences` — all required for XP tracking, autorole, and event listeners
