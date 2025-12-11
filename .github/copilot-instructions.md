# Copilot Instructions for Discord-Bot

## Project Overview
A Discord bot (using discord.py) with modular cog-based architecture. Features include prefix/slash commands, an XP-based rank system with persistent JSON storage, and per-guild welcome messages. The bot runs on `bot.py` with three core cogs: `general`, `rank`, and `welcome`.

## Architecture & Key Patterns

### Cog-Based Modularity
Each feature lives in `cogs/` as a self-contained class inheriting from `commands.Cog`:
- **Load in `setup_hook()`**: Cogs are loaded async in `bot.py`'s `setup_hook()` method before the bot connects
- **Async setup function**: Each cog must export `async def setup(bot)` to be discovered by `bot.load_extension()`
- **Example**: `cogs/rank.py` defines `class RankSystem(commands.Cog)` and ends with `async def setup(bot): await bot.add_cog(RankSystem(bot))`

### Command Types
The bot supports both patterns in single cog:
- **Slash commands**: `@app_commands.command()` — modern, auto-synced via `bot.tree.sync()` on startup
- **Prefix commands**: `@commands.command()` with `!` prefix — legacy style, auto-loaded
- See `cogs/general.py` for both examples (e.g., `/ping` slash vs `!ping` prefix)

### Data Persistence
- **Manual JSON storage** (no ORM): Utility functions `load_*()` and `save_*()` in each cog
- **File locations**: `data/ranks.json`, `data/welcome.json` (auto-create directories)
- **User IDs as strings**: Store user IDs as string keys in JSON (e.g., `ranks[str(user_id)]`)
- **Example pattern in `rank.py`**:
  ```python
  def load_ranks(): return json.load(f) if os.path.exists(RANK_FILE) else {}
  def save_ranks(data): json.dump(data, f, indent=4)
  ```

### Event Listeners & Debugging
- **Listeners**: Use `@commands.Cog.listener()` to hook events (`on_message`, `on_member_join`, etc.)
- **Logging**: `bot.py` has `on_socket_response()` for gateway event debugging; cogs log to stdout via print()
- **Error handling**: Wrap risky operations in try/except; in event handlers, don't raise—just return silently

### Admin Permissions
Commands that modify state check permissions explicitly:
```python
if not interaction.user.guild_permissions.manage_guild:
    await interaction.response.send_message("Missing permissions (manage_guild).", ephemeral=True)
    return
```

## Rank System Implementation Details

### Level Formula
- **Calculation**: `level = int((xp / 50) ** 0.5)` (in `rank.py`)
- **When to recalculate**: Whenever XP changes; `/xp_recalc` command recalculates all users' levels
- **Cooldowns**: XP awarded only once per 10 seconds per user (tracked in `self.cooldowns` dict) to prevent spam

### Data Structure
```json
{
  "user_id": {
    "xp": 1500,
    "level": 5
  }
}
```

### XP Awards
- `on_message` listener awards 15–25 XP per non-bot message (random.randint)
- Returns new level if level-up occurred; bot announces in channel
- `award_xp()` method handles XP addition and level recalculation atomically

## Welcome System

### Data Structure
Per-guild welcome config stored as:
```json
{
  "guild_id": {
    "enabled": true,
    "channel_id": 123456 or null,
    "message": "Welcome {user} to {guild}!"
  }
}
```
- `channel_id` null → DM mode; integer → post in that channel
- Message placeholders: `{user}` (mention), `{name}` (display name), `{guild}` (guild name)

### Listener & Commands
- `on_member_join` event sends configured message
- `/welcome_set`, `/welcome_set_channel`, `/welcome_toggle` manage config (require `manage_guild` perm)

## Slash Command Syncing

- **Auto-sync on startup**: `await bot.tree.sync()` in `on_ready()` event
- **Full tree** is synced every bot start (not per-guild unless needed)
- **Important**: Changes to command names/descriptions require bot restart to sync; immediate testing in Discord may show stale commands

## Development Workflow

### Setup & Running
```bash
pip install discord.py python-dotenv
# Create .env with DISCORD_TOKEN and APPLICATION_ID
python bot.py
```

### Required Intent Configuration
Must enable in both Discord Developer Portal (Bot → Privileged Gateway Intents) **and** `bot.py`:
- `Message Content Intent` (to read message text in `on_message`)
- `Server Members Intent` (for member count and member lookup)
- Current intents set in `bot.py`: `intents.message_content = True` and `intents.members = True`

### Debugging
- `bot.py` logs gateway events (`on_socket_response`); check for `INTERACTION_CREATE` events when testing slash commands
- `on_interaction` listener in `general.py` logs all interaction types for troubleshooting
- Set `logging.basicConfig(level=logging.DEBUG)` for verbose discord.py logs

### Adding New Commands
1. Create or extend a cog in `cogs/`
2. Add method decorated with `@app_commands.command()` (slash) or `@commands.command()` (prefix)
3. For slash commands: return fresh cog instance via `async def setup(bot)` if new cog
4. Load cog in `bot.py`'s `setup_hook()` via `await bot.load_extension("cogs.module_name")`
5. Restart bot to sync commands to Discord

## Common Patterns & Conventions

### String Keys for IDs
Always store user/guild IDs as strings in JSON:
```python
user_id = str(member.id)  # Convert before storage
stats = self.ranks.get(user_id, {"xp": 0, "level": 0})
```

### Ephemeral Responses for Errors/Admin
Admin-only or sensitive commands use `ephemeral=True`:
```python
await interaction.response.send_message("...", ephemeral=True)
```

### Directory Creation
Data directory auto-created at import time:
```python
os.makedirs("data", exist_ok=True)
```

### Interaction Response Pattern
Always respond to interactions immediately:
```python
await interaction.response.send_message("...")  # First response
await interaction.followup.send("...")  # Additional messages
```
If response fails, try `defer()` then `followup.send()` (see `general.py` `/test` command).

## Testing & Validation
- Test slash commands via Discord client; check `on_socket_response` logs for `INTERACTION_CREATE`
- Test prefix commands by typing in chat (requires `message_content` intent)
- Verify XP/rank changes persist by restarting bot and checking `data/ranks.json`
- Validate JSON format: `python -m json.tool data/ranks.json`
