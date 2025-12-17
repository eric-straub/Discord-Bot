# Discord-Bot

A modular, extensible Discord bot built with `discord.py`. The project uses a Cog-based design to keep features isolated, testable, and easy to extend. It includes moderation, economy, ranking, fun, trivia, casino, and per-guild settings, plus a validation script to catch common setup issues.

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

- **Modular Cogs** (`cogs/`): `general`, `economy`, `rank`, `moderation`, `trivia`, `casino`, `fun`, `games`, `settings`
- **Dual Command Support**: Slash commands (`/`) and prefix commands where appropriate
- **Rank System**: XP-based leveling with message activity tracking and leaderboards
- **Economy System**: Currency system with daily rewards, balance tracking, and casino games
- **Casino Games**: Blackjack, Slots, Roulette, Coinflip, Dice, and Crash with credit betting
- **Interactive Games**: Pong, Snake, and Conway's Game of Life with button controls
- **Trivia System**: Interactive trivia with spoiler-based answers and fuzzy matching
- **Moderation Tools**: Warnings, kicks, bans, timeouts, and message cleanup
- **Fun Commands**: Dice rolls, coin flips, 8-ball, rock-paper-scissors, and more
- **Per-Guild Settings**: Customizable prefix, XP toggle, autorole, and modlog channels
- **JSON Persistence**: All data stored as simple JSON files in `data/`
- **Pre-Flight Validation**: Built-in `validate_bot.py` to catch setup issues before deployment

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
ADMIN_IDS=123456789,987654321
```

**Note:** `ADMIN_IDS` is a comma-separated list of Discord user IDs who can use admin/moderation commands regardless of server permissions.

5. Optional: run the pre-flight validator to catch issues:

```bash
python3 validate_bot.py
```

6. Run the bot locally:

```bash
python3 bot.py
```

## Configuration

The bot uses environment variables loaded from a `.env` file in the project root:

```env
DISCORD_TOKEN=your-bot-token-here
APPLICATION_ID=your-application-id-here
ADMIN_IDS=123456789012345678,987654321098765432
```

**Environment Variables:**
- `DISCORD_TOKEN` (required): Your Discord bot token from the [Discord Developer Portal](https://discord.com/developers/applications)
- `APPLICATION_ID` (required): Your bot's application ID (found in the same portal)
- `ADMIN_IDS` (optional): Comma-separated list of Discord user IDs who bypass permission checks for admin commands

**Runtime Data:**
- Per-guild settings and user data are stored as JSON files in `data/`
- Files are created automatically on first use (e.g., `data/ranks.json`, `data/economy.json`)
- See `docs/data-format.md` for schema documentation

**Important:** Never commit your `.env` file or production data files to version control. The `.gitignore` file is configured to exclude these automatically.

## Development

### Project Structure

```
.
├── bot.py              # Main entry point, bot initialization
├── utils.py            # Shared utilities (e.g., is_admin check)
├── validate_bot.py     # Pre-flight validation script
├── requirements.txt    # Python dependencies
├── cogs/              # Feature modules (cogs)
│   ├── general.py     # Ping, help, server stats
│   ├── rank.py        # XP/leveling system
│   ├── economy.py     # Currency and daily rewards
│   ├── casino.py      # Blackjack and gambling
│   ├── trivia.py      # Trivia questions with rewards
│   ├── moderation.py  # Warns, kicks, bans, timeouts
│   ├── fun.py         # Dice, coin flip, 8ball, RPS
│   ├── games.py       # Pong, Snake, Game of Life
│   └── settings.py    # Guild configuration
├── data/              # JSON data files (auto-created)
└── docs/              # Additional documentation
```

### Creating a New Cog

Each cog follows this template structure:

```python
import discord
from discord.ext import commands
from discord import app_commands

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mycommand", description="Does something cool")
    async def my_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello!")

async def setup(bot):
    await bot.add_cog(MyCog(bot))
```

**Key Conventions:**
- Dual commands: Provide both slash (`@app_commands.command`) and prefix (`@commands.command`) when appropriate
- Admin checks: Use `utils.is_admin(user_id)` for bot-level admin permissions
- Guild permissions: Check `interaction.user.guild_permissions.*` for server-specific permissions
- Data files: Store user IDs as strings in JSON (e.g., `"123456789": {...}`)
- Cross-cog: Access other cogs via `self.bot.get_cog('CogName')` and call public methods
- Cooldowns: Use `time.time()` comparisons in instance dictionaries (see `rank.py` for example)
- Background tasks: Use `self.bot.loop.create_task()` and store task references for cleanup

See `docs/cogs.md` for more details and examples.

## Cog Details

### General (`cogs/general.py`)
- `/ping` - Check bot latency
- `/hello` - Greeting command  
- `/server_stats` - Display server information
- `/help` - Show available commands by category

### Rank System (`cogs/rank.py`)
- Automatic XP gain on message activity (15-25 XP per message, 10s cooldown)
- `/rank [member]` - View your or another user's level and XP
- `/leaderboard [page]` - Server ranking leaderboard
- `/next_level [member]` - Progress to next level with visual progress bar
- `/xp_set`, `/xp_add`, `/xp_recalc` - Admin commands for XP management
- Level formula: `level = floor(sqrt(xp / 50))`

### Economy (`cogs/economy.py`)
- `/balance [member]` - Check wallet balance
- `/daily` - Claim daily reward (100 credits, 24h cooldown)
- `/pay <member> <amount>` - Transfer credits to another user
- `/economy_set`, `/economy_add` - Admin commands for balance management

### Casino (`cogs/casino.py`)
- `/blackjack <bet>` - Play blackjack and bet credits
- Interactive game with hit/stand buttons
- 2:1 payout on blackjack, 1:1 on regular win

### Trivia (`cogs/trivia.py`)
- `/trivia_post <question> <answer> [xp] [credits] [duration]` - Post a trivia question
- Users answer using spoiler tags: `||answer||`
- Fuzzy answer matching (78% similarity threshold)
- First correct answer wins XP and credits
- `/trivia_cancel` - Cancel active trivia (asker or moderators only)

### Moderation (`cogs/moderation.py`)
- `/warn <member> [reason]` - Issue a warning
- `/warns [member]` - View warning history
- `/clear_warns <member>` - Clear all warnings
- `/kick <member> [reason]` - Kick a member
- `/ban <member> [reason]` - Ban a member
- `/timeout <member> <minutes> [reason]` - Timeout a member
- `/purge <amount>` - Delete recent messages (max 100)

### Fun (`cogs/fun.py`)
- `/dice [dice]` - Roll dice (e.g., 2d6, d20)
- `/coin` - Flip a coin
- `/rps <choice>` - Rock-paper-scissors
- `/8ball <question>` - Magic 8-ball
- `/choose <options>` - Random choice from comma-separated options

### Games (`cogs/games.py`)
- `/pong` - Play Pong with button controls (two-player paddles)
- `/snake` - Classic Snake game with directional buttons
- `/gameoflife` - Conway's Game of Life simulator with step/auto/randomize controls
- All games feature interactive button controls and auto-updates
- Only one active game per user at a time

### Settings (`cogs/settings.py`)
- `/config_show` - Display current server settings
- `/config_prefix <prefix>` - Set command prefix
- `/config_xp <enabled>` - Toggle XP system
- `/config_autorole <role>` - Set role auto-assigned to new members
- `/config_modlog <channel>` - Set moderation log channel

## Data & Persistence

### Storage Format

All runtime data is stored as JSON files in the `data/` directory:

- `ranks.json` - User XP and levels: `{"user_id": {"xp": int, "level": int}}`
- `economy.json` - User balances: `{"user_id": {"balance": int, "total_earned": int}}`  
- `settings.json` - Guild configs: `{"guild_id": {"prefix": str, "xp_enabled": bool, ...}}`
- `warns.json` - Warning records: `{"guild_id": {"user_id": [{"reason": str, ...}]}}`

### Important Notes

- Files are created automatically on first use - don't manually create empty files
- Always store Discord IDs as **strings**, never integers (JSON compatibility)
- The validator checks for malformed JSON but won't fail on missing files
- See `docs/data-format.md` for detailed schemas and examples
- Backup `data/` regularly in production environments

## Validation & Testing

### Pre-Flight Checks

Run `python3 validate_bot.py` before deploying to catch common issues:

**Environment Checks:**
- `.env` file exists and contains required variables
- `DISCORD_TOKEN` and `APPLICATION_ID` are present
- `ADMIN_IDS` is configured (warns if missing)

**File Structure:**
- Required files exist: `bot.py`, `requirements.txt`, `README.md`
- All cogs in `setup_hook()` have corresponding Python files

**Syntax Validation:**
- `bot.py` and all cog files compile without syntax errors
- Uses `python -m py_compile` for validation

**Dependencies:**
- `discord.py` is installed and version is reported
- `python-dotenv` is available

**Data Integrity:**
- Existing JSON files in `data/` are valid JSON
- Files that don't exist yet are noted (not an error)

**Security:**
- `.env` and `data/` are in `.gitignore`

### Exit Codes

- `0` - All checks passed (or warnings only)
- `1` - Critical errors found, fix before running bot

## Deployment

### Production Deployment

For production environments, use a process manager to keep the bot running:

**Option 1: systemd (Linux)**

```ini
[Unit]
Description=Discord Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/discord-bot
Environment="PATH=/opt/discord-bot/.venv/bin"
ExecStart=/opt/discord-bot/.venv/bin/python3 /opt/discord-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Option 2: Docker**

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python3", "bot.py"]
```

**Option 3: PM2 (Node.js process manager)**

```bash
pm2 start bot.py --interpreter python3 --name discord-bot
pm2 save
pm2 startup
```

### Environment Variables

- Use environment variables instead of `.env` files in production
- For Docker: pass via `-e` flags or `docker-compose.yml`
- For systemd: use `Environment=` or `EnvironmentFile=`
- Never commit secrets to version control

## Contributing

Contributions are welcome! Please follow these guidelines:

### Development Workflow

1. **Fork and clone** the repository
2. **Create a feature branch** from `dev`:
   ```bash
   git checkout -b feature/my-new-feature dev
   ```
3. **Make your changes** following project conventions
4. **Run validation**:
   ```bash
   python3 validate_bot.py
   ```
5. **Test your changes** locally with a test bot token
6. **Commit with clear messages**:
   ```bash
   git commit -m "Add: new feature description"
   ```
7. **Push and open a PR** to the `dev` branch

### Code Style

- Follow existing patterns in the codebase
- Use type hints where appropriate
- Keep cogs focused and single-purpose
- Document new commands with clear descriptions
- Store user IDs as strings in JSON files
- Use `utils.is_admin()` for admin checks
- Provide both slash and prefix commands when reasonable

### Before Submitting

- [ ] Code passes `validate_bot.py` checks
- [ ] No syntax errors (`python3 -m py_compile`)
- [ ] Tested with a real Discord bot
- [ ] Updated documentation if needed
- [ ] Followed existing code patterns
- [ ] No secrets committed (`.env`, tokens, etc.)

See `CONTRIBUTING.md` for more detailed guidelines.

## Troubleshooting

### Common Issues

**Bot doesn't start:**
- Check `.env` file exists and contains `DISCORD_TOKEN` and `APPLICATION_ID`
- Verify token is valid in Discord Developer Portal
- Run `python3 validate_bot.py` to identify issues

**Slash commands not appearing:**
- Commands sync automatically on bot startup via `bot.tree.sync()`
- Wait a few minutes for Discord to propagate changes
- Bot needs `applications.commands` scope when invited
- Check bot has proper permissions in the server

**"Missing Access" or permission errors:**
- Verify bot role is high enough in server hierarchy
- Check bot has required permissions (e.g., Manage Roles for autorole)
- Some commands require specific user permissions (e.g., Moderate Members)

**Syntax errors in cogs:**
- Run `python3 -m py_compile cogs/your_cog.py` to check specific file
- Use `validate_bot.py` to check all files at once

**Data file corruption:**
- Check `data/*.json` files are valid JSON
- Delete corrupted file - bot will recreate on next use (data will be lost)
- Keep backups of `data/` directory in production

**Cog not loading:**
- Verify cog is registered in `bot.py` `setup_hook()` method
- Check for syntax errors in the cog file
- Look for errors in bot startup console output

**XP/Economy not working:**
- Check guild settings with `/config_show`
- XP system can be disabled per-guild with `/config_xp false`
- Verify `data/ranks.json` and `data/economy.json` are valid JSON

## Useful Commands

### Development
```bash
# Validate setup before running
python3 validate_bot.py

# Run the bot
python3 bot.py

# Check syntax of a specific cog
python3 -m py_compile cogs/example.py

# Install dependencies
pip install -r requirements.txt

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### Bot Commands (In Discord)
```
# General
/ping                    # Check bot latency
/help                    # Show all commands
/server_stats           # Server information

# Economy & Ranking
/daily                   # Claim daily credits
/balance                 # Check your credits
/rank                    # View your level
/leaderboard            # Top ranked users

# Fun
/dice 2d6               # Roll dice
/8ball <question>       # Magic 8-ball
/trivia_post ...        # Post trivia question

# Moderation (requires permissions)
/warn <user> <reason>   # Warn a user
/kick <user>            # Kick a user
/timeout <user> <mins>  # Timeout a user
```

## License

This project is released under the GPLv3 License. Commercial licenses are available, Contact me. See the `LICENSE` file for more details.