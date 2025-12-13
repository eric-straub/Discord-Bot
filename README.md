# Discord-Bot

A modular, extensible Discord bot built with [discord.py](https://discordpy.readthedocs.io/), featuring moderation, economy, ranking, fun, info, trivia, welcome, and per-guild settings. Designed for easy customization and maintainability.

---

## Features

- **Modular Cogs:** Each feature is a separate cog in `cogs/` (see `docs/cogs.md`).
- **Slash & Prefix Commands:** Modern Discord slash commands (`/`) and legacy prefix commands.
- **Persistent Data:** All data stored as JSON in `data/` (see `docs/data-format.md`).
- **Per-Guild Settings:** Customizable settings for each server in `data/settings.json`.
- **Validation:** Built-in validation script to check for errors and missing files.

# Discord-Bot

A modular, extensible Discord bot built with `discord.py`. The project uses a Cog-based design to keep features isolated, testable, and easy to extend. It includes moderation, economy, ranking, fun, info, trivia, welcome, and per-guild settings, plus a validation script to catch common setup issues.

**Repository:** https://github.com/eric-straub/Discord-Bot

**Table of contents**
- Overview
- Features
- Requirements
- Quick start
- Configuration
- Development
- Cogs & extending
- Data & persistence
- Validation & testing
- Deployment
- Contributing
- License

## Overview

This bot is designed to be a clear, maintainable starting point for small-to-medium Discord servers. Key goals:

- Modular: each feature lives in its own file under `cogs/` and is loaded at runtime.
- Compatible: supports both slash (`/`) and prefix commands where useful.
- Lightweight persistence: stores per-guild and feature data as JSON under `data/`.
- Safe development flow: includes `validate_bot.py` to pre-check environment and files.

## Features

- Modular Cogs (`cogs/`): `general`, `economy`, `rank`, `moderation`, `trivia`, `welcome`, `fun`, `info`, `settings`.
- Slash + prefix command parity for many commands.
- Per-guild settings and JSON-backed data files in `data/`.
- Simple templates and docs for adding new cogs (`docs/cogs.md`).

## Requirements

- Python 3.10+ (recommended)
- See `requirements.txt` for exact pinned dependencies (primarily `discord.py` and `python-dotenv`).

## Quick start

1. Clone the repo and enter the directory:

```bash
git clone https://github.com/eric-straub/Discord-Bot.git
cd Discord-Bot
```

2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

4. Configure environment variables: create a `.env` file in the project root with the following values:

```env
DISCORD_TOKEN=your-bot-token
APPLICATION_ID=your-application-id
```

5. Optional: run the pre-flight validator to catch issues:

```bash
python3 validate_bot.py
```

6. Run the bot locally:

```bash
python3 bot.py
```

## Configuration

- The bot reads `DISCORD_TOKEN` and `APPLICATION_ID` from a `.env` file (via `python-dotenv`).
- Per-guild settings and feature data live in `data/` as JSON files (for example `data/settings.json`, `data/ranks.json`). These are created/managed by the cogs at runtime.
- Keep secrets out of version control. Use environment variables or a secrets manager in production.

## Development

- Code is organized around `commands.Cog` subclasses in `cogs/`. Each cog exposes an `async def setup(bot)` function to register itself.
- Example minimal cog (see `docs/cogs.md` for more):

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

- Run `python3 validate_bot.py` before opening PRs to ensure basic issues are caught.

## Cogs & extending

- To add a new feature, create a new file in `cogs/` and implement a Cog class with a `setup` factory.
- Prefer providing both a slash command and a prefix command when it makes sense for parity.
- Register the cog loading in `bot.py`'s `setup_hook()` if it should load by default.

## Data & persistence

- All runtime data is stored as JSON files under `data/`.
- Small helper cogs read/write these files using `json.load`/`json.dump` patterns.
- `docs/data-format.md` documents expected schemas for important files (e.g., `data/ranks.json`).

## Validation & testing

- Use `python3 validate_bot.py` to perform pre-flight checks: missing env vars, syntax errors in cogs, and malformed JSON in `data/`.
- The validator aims to be lightweight — fix issues locally and re-run before deploying.

## Deployment

- For production, run the bot under a process manager such as `systemd`, `supervisord`, or inside a Docker container.
- Ensure environment variables are injected securely (don't commit `.env` to the repo).

Example `systemd` unit (illustrative, adapt paths):

```ini
[Unit]
Description=Discord Bot
After=network.target

[Service]
WorkingDirectory=/srv/discord-bot
ExecStart=/srv/discord-bot/.venv/bin/python /srv/discord-bot/bot.py
Restart=always
User=botuser

[Install]
WantedBy=multi-user.target
```

## Contributing

- Branch from `dev` and open PRs back into `dev`.
- Keep commits small and focused.
- Run `python3 validate_bot.py` and ensure your cog follows the `docs/cogs.md` template.
- See `CONTRIBUTING.md` for more details on the contribution workflow.

## Troubleshooting

- Bot doesn't start: check `.env` for `DISCORD_TOKEN` and `APPLICATION_ID`.
- Syntax error in a cog: run `python -m py_compile cogs/your_cog.py` or rely on `validate_bot.py`.
- Missing data file: many data files are created lazily; check `data/jsons_go_here.txt` for intended filenames and initial schemas.

## Useful commands

- Validate setup: `python3 validate_bot.py`
- Run bot locally: `python3 bot.py`
- Check a single cog for syntax: `python -m py_compile cogs/your_cog.py`

## License

This project is released under the GPLv3 License. Commercial licenses are available, Contact me. See the `LICENSE` file for more details.