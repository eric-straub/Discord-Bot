# Discord-Bot

A lightweight, single-process Discord bot built with discord.py. This repository provides a modular cog-based bot, runtime JSON storage for simple persistent state, and helper scripts to validate and run the bot locally.

## Features

- Modular cogs in `cogs/` (commands organized by feature)
- Slash commands using `discord.app_commands`
- Simple JSON-backed runtime storage in `data/`
- Pre-flight validation script (`validate_bot.py`) to check environment and repo health

## Quick Start

Requirements:

- Python 3.8+ (use the interpreter available on your system)
- `pip` and a virtual environment recommended

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Create a `.env` file in the project root containing the required secrets:

```text
DISCORD_TOKEN=<your-bot-token>
APPLICATION_ID=<your-application-id>
```

Validate the repo (syntax, env, and JSON checks):

```bash
python3 validate_bot.py
```

Run the bot locally:

```bash
python3 bot.py
```

If you change slash commands, sync them from the bot by ensuring the bot connects and `bot.tree.sync()` runs on ready.

## Project Structure

- `bot.py` — Bot entrypoint. Defines `MyBot`, intents, and loads cogs in `setup_hook()`.
- `cogs/` — Feature modules. Each cog exports a `commands.Cog` subclass and an `async def setup(bot)` function that adds the cog.
- `data/` — Runtime JSON storage (e.g., `ranks.json`). Files are created on first use.
- `validate_bot.py` — Pre-flight validation script (checks `.env`, syntax, and JSON files).
- `requirements.txt` — Python dependencies.

## Working with Cogs

Pattern for a cog:

- Define a `class MyCog(commands.Cog)` with commands and listeners.
- Export `async def setup(bot): await bot.add_cog(MyCog(bot))` at the bottom of the cog file.

When adding a new cog, register its loading in `MyBot.setup_hook()` in `bot.py` by adding:

```py
await self.load_extension("cogs.yourcog")
```

Slash command pattern:

```py
@app_commands.command(name="userinfo")
async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
    await interaction.response.send_message(...)
```

## Data & Configuration

- Secrets: store `DISCORD_TOKEN` and `APPLICATION_ID` in `.env`. The validator expects `.env` to exist.
- Persistent runtime data is stored as JSON under `data/` (e.g., `data/ranks.json`). The project will create missing files on first use but will warn on invalid JSON.

## Development

Recommended workflow:

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run `python3 -m py_compile bot.py` or `python3 validate_bot.py` to check for syntax issues.
4. Add your cog to `cogs/` and register it in `bot.py`.

Useful commands:

```bash
# Syntax check for a specific file
python3 -m py_compile cogs/yourcog.py

# Run the validator script
python3 validate_bot.py

# Start the bot
python3 bot.py
```

## Testing & Validation

- `validate_bot.py` performs pre-flight checks including environment variable presence, basic syntax checks, and JSON validation for files under `data/`.
- When adding new cogs or changing data formats, run `python3 validate_bot.py` before starting the bot.

## Contributing

Contributions are welcome. Suggested process:

1. Open an issue to discuss larger changes.
2. Create a feature branch from `dev`.
3. Add or update code and tests where applicable.
4. Run `python3 validate_bot.py` and any linting or formatting tools you use.
5. Open a pull request describing the change and any manual steps required.

When adding new public-facing commands, include usage examples and permission expectations in your PR description.

## Deployment & Hosting Notes

- For production hosting, ensure environment secrets are provided via a secure environment mechanism (not committed to the repo).
- Consider running the bot under a process manager (systemd, supervisord, Docker) and restart-on-failure policies.

## License

This repository does not include an explicit license file. If you plan to publish or share this project, add a `LICENSE` file with your chosen license.

## Contact

For questions about the project, open an issue or reach out to the repository owner.

---

If you'd like, I can also:

- Add a short `CONTRIBUTING.md` and a sample `LICENSE`.
- Commit and push this README to `dev` and open a PR.

If you want me to proceed with committing and pushing, tell me and I will do that next.
