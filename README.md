# Discord Bot

A fully-featured Discord bot built with **discord.py** featuring XP/rank system, economy, moderation, and more.

## Overview

This bot includes:
- **Slash & prefix commands** for flexibility
- **XP + leveling system** with automatic rank tracking
- **Currency economy** with daily rewards and transfers
- **Moderation tools** (warnings, timeouts, message purge)
- **Fun commands** (dice, games, magic 8-ball)
- **Server-wide configuration** (welcome messages, settings, autorole)
- **Persistent JSON storage** (no database required)

---

## Project Structure

```
Discord-Bot/
├── bot.py               # Main entry point & event handlers
├── cogs/                # Modular feature modules
│   ├── general.py       # Utility commands (ping, help, status)
│   ├── rank.py          # XP system & leaderboards
│   ├── welcome.py       # New member greeting
│   ├── fun.py           # Games & entertainment
│   ├── info.py          # User & server info
│   ├── moderation.py    # Warnings, timeouts, purge
│   ├── economy.py       # Currency & wallets
│   └── settings.py      # Server configuration
└── data/                # Persistent storage (auto-created)
    ├── ranks.json       # User XP & levels
    ├── economy.json     # Wallet balances
    ├── welcome.json     # Per-guild welcome config
    ├── warns.json       # Moderation warnings
    └── settings.json    # Server settings
```

---

## Quick Start

### 1. Install Dependencies
```bash
pip install discord.py python-dotenv
```

### 2. Create `.env` File
```env
DISCORD_TOKEN=your_bot_token
APPLICATION_ID=your_app_id
```

### 3. Enable Intents in Discord Developer Portal
- ✅ Message Content Intent
- ✅ Server Members Intent

### 4. Run the Bot
```bash
python bot.py
```

---

## Command Summary

### General Commands

**Slash**: `/ping` `/hello` `/test` `/server_stats` `/help` `/status`
**Prefix**: `!ping` `!echo <text>`

---

### XP + Rank System

Users earn XP automatically by chatting.

* XP gain: **15–25 XP per message**
* Cooldown: **10 seconds per user**
* Level formula: `level = sqrt(xp / 50)`

**Commands**: `/rank` `/profile` `/leaderboard` `/topranks` `/xp_leaderboard` `/next_level` `/xp_set` `/xp_add` `/xp_recalc`

---

### Welcome System

Greet new members with custom messages. Per-guild configuration with placeholders: `{user}`, `{name}`, `{guild}`.

**Commands**: `/welcome_set` `/welcome_set_channel` `/welcome_toggle` `/welcome_show` `/welcome_help`

---

### Fun & Games

**Commands**: `/dice [NdX]` `/coin` `/rps <choice>` `/8ball <question>` `/choose <options>`

---

### User & Server Info

**Commands**: `/userinfo` `/serverinfo` `/avatar` `/whois` `/roles`

---

### Moderation (Requires `moderate_members`)

Warnings with history, timeouts, and message cleanup.

**Commands**: `/warn` `/warns` `/clearwarn` `/timeout` `/untimeout` `/purge`

---

### Economy (Currency)

Simple currency with daily rewards and transfers.

* Currency: 🪙 **Credits**
* Daily bonus: **100 Credits** (once per 24h)

**Commands**: `/balance` `/daily` `/pay` `/rich` `/give_currency` `/reset_economy`

---

### Server Settings (Requires `administrator`)

Per-server configuration: XP toggle, welcome messages, autorole, modlog channel.

**Commands**: `/config_show` `/set_xp_enabled` `/set_modlog_channel` `/set_autorole`

---

## Requirements

Install dependencies:

```
pip install discord.py python-dotenv
```

Make sure your bot has the following **intents enabled**:

* Message Content Intent
* Server Members

These must be enabled both in:

### 1. *Discord Developer Portal → Bot → Privileged Gateway Intents*

### 2. Your code (`bot.py`):

```python
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
```

---

## Environment Configuration

Create a `.env` file:

```
DISCORD_TOKEN=YOUR_BOT_TOKEN
APPLICATION_ID=YOUR_APPLICATION_ID
```

Where:

* `DISCORD_TOKEN` = Bot token from the Developer Portal
* `APPLICATION_ID` = The bot's application ID (same page)

---

## Running the Bot

```
python3 bot.py
```

On startup, you should see:

```
Slash commands synced.
Bot is ready.
```

The bot automatically:

* Loads cogs
* Registers slash commands
* Syncs the application command tree on startup


## Logging

The bot logs:

* Gateway events (`INTERACTION_CREATE`, etc.)
* All received interactions
* Errors in any command or listener

This makes debugging slash commands significantly easier.

---

## Contributing

Pull requests are welcome!
To add a new command, create a new cog in `cogs/` and load it via `setup_hook` in `bot.py`.

---

## License

MIT License.

