# Setup & Running

This document provides comprehensive setup instructions for development, testing, and production deployment.

## Prerequisites

- **Python 3.10 or higher** (3.11+ recommended)
- **pip** package manager
- **Discord bot application** from [Discord Developer Portal](https://discord.com/developers/applications)
- **Git** (for cloning repository)

## Getting a Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" tab and click "Add Bot"
4. Under "Token", click "Reset Token" and copy it (save it securely!)
5. Enable these **Privileged Gateway Intents**:
   - ✅ Server Members Intent
   - ✅ Message Content Intent
   - ✅ Presence Intent
6. Go to "OAuth2" → "General" and copy your **Application ID**
7. Go to "OAuth2" → "URL Generator":
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Administrator` (or specific permissions needed)
   - Copy the generated URL and invite bot to your test server

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/eric-straub/Discord-Bot.git
cd Discord-Bot
```

### 2. Create Virtual Environment

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install discord.py python-dotenv
```

### 4. Create Configuration File

Create a `.env` file in the project root:

```bash
touch .env  # Linux/macOS
type nul > .env  # Windows
```

Add your credentials:
```env
DISCORD_TOKEN=your-bot-token-here
APPLICATION_ID=your-application-id-here
ADMIN_IDS=your-user-id,another-user-id
```

**Finding your User ID:**
1. Enable Developer Mode in Discord: Settings → Advanced → Developer Mode
2. Right-click your username and select "Copy User ID"

### 5. Validate Setup

```bash
python3 validate_bot.py
```

Expected output:
```
🤖 Discord Bot - Pre-Flight Validator

📋 Checking environment...
✅ .env file exists
✅ .env contains DISCORD_TOKEN
✅ .env contains APPLICATION_ID
...
✅ All checks passed! Bot is ready to run.
```

### 6. Run the Bot

```bash
python3 bot.py
```

Expected output:
```
Logged in as YourBot#1234 (ID: 123456789012345678)
Slash commands synced.
Bot is ready.
```

### 7. Test Commands

In your Discord server:
- `/ping` - Check if bot responds
- `/help` - View all available commands
- `/server_stats` - View server information

## Project Structure

```
Discord-Bot/
├── bot.py              # Main entry point
├── utils.py            # Shared utilities (is_admin)
├── validate_bot.py     # Pre-flight validator
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create this)
├── .gitignore         # Git ignore rules
├── README.md          # Main documentation
├── cogs/              # Feature modules
│   ├── general.py     # Basic commands
│   ├── rank.py        # XP/leveling system
│   ├── economy.py     # Currency system
│   ├── casino.py      # Gambling games
│   ├── trivia.py      # Trivia system
│   ├── moderation.py  # Mod tools
│   ├── fun.py         # Fun commands
│   └── settings.py    # Guild configuration
├── data/              # JSON data files (auto-created)
│   ├── jsons_go_here.txt
│   ├── ranks.json     # (created on first XP gain)
│   ├── economy.json   # (created on first /daily)
│   ├── warns.json     # (created on first /warn)
│   └── settings.json  # (created on first /config_*)
└── docs/              # Documentation
    ├── cogs.md        # Cog development guide
    ├── data-format.md # Data file schemas
    ├── setup.md       # This file
    └── validation.md  # Validator documentation
```

## Development Workflow

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-feature dev
   ```

2. **Edit code** (e.g., add a new cog in `cogs/`)

3. **Validate changes:**
   ```bash
   python3 validate_bot.py
   ```

4. **Test locally:**
   ```bash
   python3 bot.py
   ```

5. **Commit and push:**
   ```bash
   git add .
   git commit -m "Add: description of changes"
   git push origin feature/my-feature
   ```

### Hot Reload During Development

The bot doesn't support hot reload by default. To test changes:
1. Stop the bot (Ctrl+C)
2. Make your changes
3. Run `python3 validate_bot.py`
4. Restart: `python3 bot.py`

## Production Deployment

### Option 1: systemd (Linux)

Create `/etc/systemd/system/discord-bot.service`:

```ini
[Unit]
Description=Discord Bot
After=network.target

[Service]
Type=simple
User=botuser
Group=botuser
WorkingDirectory=/opt/discord-bot
Environment="DISCORD_TOKEN=your-token-here"
Environment="APPLICATION_ID=your-app-id-here"
Environment="ADMIN_IDS=123456789012345678"
ExecStart=/opt/discord-bot/.venv/bin/python3 /opt/discord-bot/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Start and enable:**
```bash
sudo systemctl daemon-reload
sudo systemctl start discord-bot
sudo systemctl enable discord-bot
sudo systemctl status discord-bot
```

**View logs:**
```bash
sudo journalctl -u discord-bot -f
```

### Option 2: Docker

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run validation and bot
CMD ["sh", "-c", "python3 validate_bot.py && python3 bot.py"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  discord-bot:
    build: .
    container_name: discord-bot
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - APPLICATION_ID=${APPLICATION_ID}
      - ADMIN_IDS=${ADMIN_IDS}
    volumes:
      - ./data:/app/data
```

**Run with Docker Compose:**
```bash
# Create .env file with credentials
docker-compose up -d
docker-compose logs -f
```

### Option 3: PM2 (Cross-platform)

Install PM2:
```bash
npm install -g pm2
```

Create `ecosystem.config.js`:
```javascript
module.exports = {
  apps: [{
    name: 'discord-bot',
    script: 'bot.py',
    interpreter: 'python3',
    cwd: '/opt/discord-bot',
    env: {
      DISCORD_TOKEN: 'your-token-here',
      APPLICATION_ID: 'your-app-id-here',
      ADMIN_IDS: '123456789012345678'
    },
    error_file: 'logs/err.log',
    out_file: 'logs/out.log',
    time: true
  }]
};
```

**Start bot:**
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Enable on system boot
```

## Environment Variables

### Required
- `DISCORD_TOKEN` - Your bot token from Discord Developer Portal
- `APPLICATION_ID` - Your application ID (for slash commands)

### Optional
- `ADMIN_IDS` - Comma-separated Discord user IDs with admin access
  - Example: `123456789012345678,987654321098765432`
  - Users in this list bypass permission checks for admin commands

## Security Best Practices

### Never Commit Secrets
```bash
# Verify .gitignore includes:
.env
data/
__pycache__/
*.pyc
```

### Use Environment Variables in Production
Instead of `.env` files, use:
- systemd `Environment=` directives
- Docker secrets or environment variables
- Cloud provider secret managers (AWS Secrets Manager, etc.)

### Restrict Bot Permissions
Only grant Discord permissions the bot actually needs:
- ✅ Send Messages
- ✅ Embed Links
- ✅ Read Message History
- ✅ Use Slash Commands
- ✅ Moderate Members (for moderation features)
- ❌ Administrator (unless absolutely necessary)

### Regular Updates
```bash
# Update dependencies regularly
pip install --upgrade -r requirements.txt

# Check for security vulnerabilities
pip check
```

## Troubleshooting Setup

### "Module not found" errors
```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Bot doesn't respond to slash commands
- Wait 5-10 minutes for Discord to sync commands globally
- Check bot has `applications.commands` scope
- Verify bot has required permissions in server
- Try kicking and re-inviting the bot

### "Invalid token" error
- Verify `DISCORD_TOKEN` in `.env` is correct
- Token may have been regenerated in Developer Portal
- Check for extra spaces or quotes in `.env`

### Slash commands work but prefix commands don't
- Check guild settings: `/config_show`
- Default prefix is `!`, change with `/config_prefix`
- Verify message content intent is enabled

### Data files not persisting
- Check `data/` directory exists and is writable
- Verify not running from read-only filesystem
- Check logs for JSON write errors

## Performance Tuning

### For Small Servers (< 1000 members)
Default configuration works well.

### For Larger Servers
Consider:
- Disabling XP gain with `/config_xp false` to reduce database writes
- Using a proper database instead of JSON (requires code changes)
- Horizontal scaling with sharding (advanced, requires code changes)

## Backup and Recovery

### Backup Data
```bash
# Create backup
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Automated daily backup (cron)
0 2 * * * cd /opt/discord-bot && tar -czf backup-$(date +\%Y\%m\%d).tar.gz data/
```

### Restore Data
```bash
# Stop bot
sudo systemctl stop discord-bot  # or docker-compose down

# Restore
tar -xzf backup-20251215.tar.gz

# Start bot
sudo systemctl start discord-bot  # or docker-compose up -d
```

## Getting Help

- **Documentation**: Check `docs/` folder
- **Validation**: Run `python3 validate_bot.py`
- **Logs**: Check console output or system logs
- **Issues**: Report bugs on GitHub repository
- **Discord API**: https://discord.com/developers/docs
