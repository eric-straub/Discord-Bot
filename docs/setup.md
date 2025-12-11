# Setup & Running

This document expands the Quick Start guide in `README.md` with more details for development, testing, and production hosting.

## Local Development

1. Install Python 3.8+ and `pip`.
2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

4. Create `.env` with your credentials:

```text
DISCORD_TOKEN=<your-bot-token>
APPLICATION_ID=<your-application-id>
```

5. Validate and run:

```bash
python3 validate_bot.py
python3 bot.py
```

## Running in Production

- Use secure environment variable management (secrets manager, CI/CD variables, or systemd environment files).
- Run under a process manager (systemd, supervisord) or containerize with Docker.

### Example systemd service snippet

```ini
[Unit]
Description=Discord Bot
After=network.target

[Service]
User=botuser
WorkingDirectory=/path/to/Discord-Bot
Environment=DISCORD_TOKEN=___
Environment=APPLICATION_ID=___
ExecStart=/path/to/venv/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Docker (optional)

If you want to run the bot in Docker, create a simple `Dockerfile` and pass secrets as environment variables at runtime. Keep images up-to-date and secure.
