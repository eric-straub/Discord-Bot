## Overview

This Discord bot is built using **discord.py**, supports both **prefix commands** (`!ping`, `!echo`, etc.) and **slash commands** (`/ping`, `/rank`, `/leaderboard`, etc.), and includes a complete **XP + leveling rank system**.

It uses a modular architecture with **cogs**, automatic command syncing, event logging for debugging, and persistent storage through JSON files.

---

## Project Structure

```
Discord-Bot/
│
├── bot.py               # Main entry point
├── data/
│   └── ranks.json       # Stored XP + Level data (auto-created)
└── cogs/
    ├── general.py       # General commands (prefix + slash)
    └── rank.py          # Rank system + leaderboard
```

---

## Features

### General Commands

| Type   | Command        | Description                               |
| ------ | -------------- | ----------------------------------------- |
| Slash  | `/ping`        | Show latency                              |
| Slash  | `/hello`       | Say hello                                 |
| Slash  | `/test`        | Tests slash command functionality         |
| Prefix | `!ping`        | Checks latency using prefix-style command |
| Prefix | `!echo <text>` | Repeats your message                      |

---

### XP + Rank System

Users earn XP automatically by chatting.

* XP gain: **15–25 XP per message**
* Cooldown: **10 seconds per user**
* Level formula:

  ```
  level = sqrt(xp / 50)
  ```
* Level-up announcements in the channel
* Data saved persistently to `data/ranks.json`

#### Slash Commands

| Command        | Description                |
| -------------- | -------------------------- |
| `/rank`        | Check your level + XP      |
| `/rank @user`  | Check someone else’s stats |
| `/leaderboard` | Shows top 10 users by XP   |

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

---

## Testing the Rank System

### Award XP

Send a message in any channel.

### Test Cooldown

Send a second message within 10 seconds → no XP should be awarded.

### Check leveling

Edit `data/ranks.json` manually to simulate values and trigger level-ups.

### Slash command testing

```
/rank
/rank @user
/leaderboard
/test
```

---

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

