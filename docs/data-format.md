# Data Formats

This file describes the JSON-backed runtime data files stored under `data/`. These files are simple JSON objects used for persistent state (ranks, economy, settings, etc.).

## `data/ranks.json`

`ranks.json` maps a Discord user ID (string) to an object containing `xp` and `level`.

Example (from repository):

```json
{
    "89161521543811072": {
        "xp": 58,
        "level": 1
    }
}
```

Notes:

- Keys are always user IDs as strings.
- `xp` is typically an integer representing accumulated experience points.
- `level` is an integer representing the user's current level.
- Code that reads/writes these files should handle the case where the file is missing (the application will create it on first use) and handle invalid JSON by regenerating or warning the operator.

## Other JSON files

- `data/economy.json` — stores user balances and transaction history (format depends on economy cog implementation).
- `data/welcome.json` — configuration for welcome messages per guild.
- `data/warns.json` — warnings and moderation records per user/guild.
- `data/settings.json` — bot-level and guild-level configuration keys.

When adding new fields, document the change here and include a migration plan in the PR if existing deployments are affected.
