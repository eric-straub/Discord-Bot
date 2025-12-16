# Cogs & Commands

This guide explains how to create, register, and extend cogs in the Discord bot.

## What are Cogs?

Cogs are modular components that group related commands and functionality. Each cog is a Python class that inherits from `commands.Cog` and is loaded dynamically at runtime.

**Benefits:**
- Organize features into logical modules
- Easy to enable/disable features
- Reload cogs without restarting the bot (in development)
- Share state and utilities within a cog

## Current Cogs

- `general.py` - Basic commands (ping, hello, help, server stats)
- `rank.py` - XP and leveling system with leaderboards
- `economy.py` - Currency system with daily rewards and transfers
- `casino.py` - Gambling games (blackjack)
- `trivia.py` - Interactive trivia with rewards
- `moderation.py` - Moderation tools (warn, kick, ban, timeout)
- `fun.py` - Entertainment commands (dice, 8ball, RPS)
- `settings.py` - Per-guild configuration

## Creating a New Cog

### Basic Template

Create a new file in `cogs/`, for example `cogs/example.py`:

```python
import discord
from discord.ext import commands
from discord import app_commands

class Example(commands.Cog):
    """Description of what this cog does."""
    
    def __init__(self, bot):
        self.bot = bot
        # Initialize any state here
        self.my_data = {}
    
    @app_commands.command(name="hello", description="Say hello")
    async def hello(self, interaction: discord.Interaction):
        """Slash command - responds to /hello."""
        await interaction.response.send_message(f"Hello, {interaction.user.mention}!")
    
    @commands.command(name="hello")
    async def hello_prefix(self, ctx):
        """Prefix command - responds to !hello."""
        await ctx.send(f"Hello, {ctx.author.mention}!")

async def setup(bot):
    """Required setup function to register the cog."""
    await bot.add_cog(Example(bot))
```

### Registering the Cog

Add the cog to `bot.py` in the `setup_hook()` method:

```python
async def setup_hook(self):
    """Runs before the bot connects — load cogs here."""
    await self.load_extension("cogs.general")
    await self.load_extension("cogs.example")  # Add your new cog
    # ... other cogs
```

## Command Types

### Slash Commands (Modern)

```python
@app_commands.command(name="mycommand", description="What this command does")
async def my_command(self, interaction: discord.Interaction, argument: str = "default"):
    """Slash command implementation."""
    await interaction.response.send_message(f"You said: {argument}")
```

**Key points:**
- Use `@app_commands.command` decorator
- Takes `interaction: discord.Interaction` as first parameter
- Respond with `interaction.response.send_message()`
- For long operations, use `await interaction.response.defer()` first
- Parameters become command options automatically

### Prefix Commands (Legacy)

```python
@commands.command(name="mycommand")
async def my_command_prefix(self, ctx, argument: str = "default"):
    """Prefix command implementation."""
    await ctx.send(f"You said: {argument}")
```

**Key points:**
- Use `@commands.command` decorator
- Takes `ctx` (context) as first parameter
- Respond with `ctx.send()`
- Prefix is configurable per-guild (default: `!`)

## Advanced Patterns

### Event Listeners

```python
@commands.Cog.listener()
async def on_message(self, message: discord.Message):
    """Listen to all messages."""
    if message.author.bot:
        return
    # Process message
    print(f"Message from {message.author}: {message.content}")
```

### Admin-Only Commands

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import is_admin

@app_commands.command(name="admin_only", description="Admin command")
async def admin_only(self, interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("Admin only!", ephemeral=True)
        return
    # Admin logic here
```

### Permission Checks

```python
@app_commands.command(name="mod_only", description="Moderator command")
async def mod_only(self, interaction: discord.Interaction):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("Missing permissions!", ephemeral=True)
        return
    # Moderator logic here
```

### Cooldowns

Use a dictionary to track cooldowns:

```python
import time

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}  # user_id -> timestamp
    
    @app_commands.command(name="limited", description="Command with cooldown")
    async def limited(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        now = time.time()
        
        last_use = self.cooldowns.get(user_id, 0)
        if now - last_use < 60:  # 60 second cooldown
            remaining = 60 - (now - last_use)
            await interaction.response.send_message(
                f"Cooldown! Try again in {remaining:.0f}s", 
                ephemeral=True
            )
            return
        
        self.cooldowns[user_id] = now
        await interaction.response.send_message("Command executed!")
```

### Cross-Cog Communication

Access other cogs via `self.bot.get_cog('CogName')`:

```python
@app_commands.command(name="award", description="Give XP and credits")
async def award(self, interaction: discord.Interaction, user: discord.Member):
    rank_cog = self.bot.get_cog('RankSystem')
    economy_cog = self.bot.get_cog('Economy')
    
    if rank_cog:
        await rank_cog.award_xp(user.id, 100)
    
    if economy_cog:
        economy_cog._add_balance(user.id, 50)
    
    await interaction.response.send_message(f"Awarded {user.mention}!")
```

### Background Tasks

Use `self.bot.loop.create_task()` for async background work:

```python
class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_tasks = {}
    
    async def my_background_task(self, task_id):
        """Background task that runs asynchronously."""
        try:
            await asyncio.sleep(60)
            # Do something after 60 seconds
            print(f"Task {task_id} completed")
        except asyncio.CancelledError:
            print(f"Task {task_id} cancelled")
    
    @app_commands.command(name="start_task", description="Start background task")
    async def start_task(self, interaction: discord.Interaction):
        task_id = interaction.user.id
        task = self.bot.loop.create_task(self.my_background_task(task_id))
        self.active_tasks[task_id] = task
        await interaction.response.send_message("Task started!")
    
    def cog_unload(self):
        """Cleanup when cog is unloaded."""
        for task in self.active_tasks.values():
            if not task.done():
                task.cancel()
```

### Persistent Data

Load and save JSON data:

```python
import json
import os

DATA_FILE = "data/mycog.json"
os.makedirs("data", exist_ok=True)

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self._load_data()
    
    def _load_data(self):
        """Load data from JSON file."""
        if not os.path.exists(DATA_FILE):
            return {}
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    
    def _save_data(self):
        """Save data to JSON file."""
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=4)
    
    @app_commands.command(name="save_value", description="Save a value")
    async def save_value(self, interaction: discord.Interaction, value: str):
        user_id = str(interaction.user.id)  # Store IDs as strings!
        self.data[user_id] = value
        self._save_data()
        await interaction.response.send_message(f"Saved: {value}")
```

## Best Practices

### Do's
✅ Keep cogs focused on a single feature area  
✅ Provide both slash and prefix commands when appropriate  
✅ Use descriptive command names and descriptions  
✅ Store Discord IDs as **strings** in JSON  
✅ Handle errors gracefully and provide user feedback  
✅ Use `ephemeral=True` for error messages  
✅ Document your code with docstrings  
✅ Validate user input before processing  
✅ Use `await interaction.response.defer()` for slow operations  

### Don'ts
❌ Don't store secrets or tokens in cog files  
❌ Don't use blocking operations without `asyncio.to_thread()`  
❌ Don't forget to cancel background tasks on unload  
❌ Don't hardcode guild or channel IDs (make configurable)  
❌ Don't assume other cogs are loaded (check with `get_cog()`)  
❌ Don't modify data files while bot is running (race conditions)  
❌ Don't use heavy logging frameworks (prefer simple prints)  

## Testing Your Cog

1. **Syntax check:**
   ```bash
   python3 -m py_compile cogs/mycog.py
   ```

2. **Run validator:**
   ```bash
   python3 validate_bot.py
   ```

3. **Test with bot:**
   - Create a test Discord server
   - Invite your bot with appropriate permissions
   - Test all command paths (success and error cases)
   - Check data file creation and formatting

4. **Check logs:**
   - Watch console output for errors
   - Verify slash command sync happens
   - Confirm cog loads without errors

## Common Issues

**Cog not loading:**
- Check syntax errors with `python3 -m py_compile`
- Verify `setup()` function exists and is async
- Ensure cog is registered in `bot.py`

**Commands not appearing:**
- Wait for slash command sync (automatic on startup)
- Check bot has `applications.commands` scope
- Verify command names are unique

**Import errors:**
- Use relative imports or add parent directory to path
- Check all dependencies are installed

**Data not persisting:**
- Ensure you call `_save_data()` after changes
- Verify `data/` directory exists and is writable
- Check file isn't corrupted (run validator)
