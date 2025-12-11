# Cogs & Commands

This guide explains how to add commands, create cogs, and register them with the bot.

## Cog Template

Create a new file in `cogs/`, for example `cogs/example.py`:

```py
from discord.ext import commands
from discord import app_commands

class Example(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="hello")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Example(bot))
```

## Registering a Cog

Add the cog to `MyBot.setup_hook()` in `bot.py` so it loads on startup:

```py
await self.load_extension("cogs.example")
```

## Slash Commands

- Use `@app_commands.command(...)` to define slash commands that accept an `interaction: discord.Interaction`.
- Use `await interaction.response.send_message(...)` to reply.

## Best Practices

- Keep cogs focused by feature (e.g., `economy.py`, `rank.py`).
- Reuse helper functions inside a cog rather than copying logic between commands.
- Document user-visible commands with usage examples and permission expectations.
