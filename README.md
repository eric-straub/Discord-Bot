# Discord-Bot

A modular, extensible Discord bot built with [discord.py](https://discordpy.readthedocs.io/), featuring moderation, economy, ranking, fun, info, trivia, welcome, and per-guild settings. Designed for easy customization and maintainability.

---

## Features

- **Modular Cogs:** Each feature is a separate cog in `cogs/` (see `docs/cogs.md`).
- **Slash & Prefix Commands:** Modern Discord slash commands (`/`) and legacy prefix commands.
- **Persistent Data:** All data stored as JSON in `data/` (see `docs/data-format.md`).
- **Per-Guild Settings:** Customizable settings for each server in `data/settings.json`.
- **Validation:** Built-in validation script to check for errors and missing files.

---

## Quick Start

1. **Clone the repo:**
   ```bash
   git clone https://github.com/eric-straub/Discord-Bot.git
   cd Discord-Bot
   ```
2. **Set up a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   python3 -m pip install -r requirements.txt
   ```
4. **Configure environment variables:**
   - Create a `.env` file with:
     ```env
     DISCORD_TOKEN=your-bot-token
     APPLICATION_ID=your-app-id
     ```
5. **Validate setup:**
   ```bash
   python3 validate_bot.py
   ```
6. **Run the bot:**
   ```bash
   python3 bot.py
   ```

---

## Project Structure

```
Discord-Bot/
├── bot.py                # Main entry point
├── cogs/                 # Feature modules (cogs)
├── data/                 # Persistent JSON data
├── docs/                 # Extended documentation
├── requirements.txt       # Python dependencies
├── validate_bot.py        # Validation script
└── ...
```

- **See `docs/` for:**
  - Setup & deployment (`setup.md`)
  - Cog development (`cogs.md`)
  - Data formats (`data-format.md`)
  - Validation details (`validation.md`)

---

## Adding Features

- **New Cog:**
  1. Create a new file in `cogs/` (see `docs/cogs.md` for template).
  2. Register it in `MyBot.setup_hook()` in `bot.py`.
  3. If using new data files, create them in `data/` and document in `docs/data-format.md`.
  4. Update `validate_bot.py` to check new files/cogs.

- **New Commands:**
  - Prefer `@app_commands.command` for slash commands.
  - Use type hints where helpful.
  - Document new commands and data changes in `docs/`.

---

## Contributing

- Branch from `dev`.
- Use small, focused commits.
- Follow code style and documentation conventions (see `CONTRIBUTING.md`).
- Run `python3 validate_bot.py` before submitting PRs.

---

## Deployment

- For production, use a process manager (systemd, Docker, etc.).
- Securely manage environment variables.
- See `docs/setup.md` for details.

---

## License

[MIT](LICENSE)

---

## Credits

- Built with [discord.py](https://discordpy.readthedocs.io/)
- See `CONTRIBUTING.md` for contributors and guidelines.
