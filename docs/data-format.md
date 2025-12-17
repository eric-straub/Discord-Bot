# Data Formats

This document describes the JSON-backed data files stored in `data/`. These files persist bot state across restarts and are managed automatically by the cogs.

## General Guidelines

- **User IDs**: Always stored as strings (e.g., `"123456789012345678"`), never integers
- **Guild IDs**: Also stored as strings for consistency
- **Auto-creation**: Files are created automatically on first use - don't manually create empty files
- **Validation**: Run `python3 validate_bot.py` to check for malformed JSON
- **Backups**: In production, regularly backup the entire `data/` directory

## File Schemas

### `data/ranks.json`

Maps user IDs to XP and level data.

**Schema:**
```json
{
  "user_id_string": {
    "xp": integer,
    "level": integer
  }
}
```

**Example:**
```json
{
  "89161521543811072": {
    "xp": 58,
    "level": 1
  },
  "123456789012345678": {
    "xp": 2500,
    "level": 7
  }
}
```

**Notes:**
- `xp`: Total experience points accumulated
- `level`: Current level, calculated as `floor(sqrt(xp / 50))`
- XP is gained from messages (15-25 per message, 10-second cooldown per user)
- Managed by `cogs/rank.py`

### `data/economy.json`

Stores user currency balances and total earnings.

**Schema:**
```json
{
  "user_id_string": {
    "balance": integer,
    "total_earned": integer
  }
}
```

**Example:**
```json
{
  "89161521543811072": {
    "balance": 450,
    "total_earned": 1200
  }
}
```

**Notes:**
- `balance`: Current credits available for spending
- `total_earned`: Lifetime earnings (never decreases, only increases)
- Daily reward: 100 credits with 24-hour cooldown
- Managed by `cogs/economy.py`

### `data/settings.json`

Per-guild configuration settings.

**Schema:**
```json
{
  "guild_id_string": {
    "prefix": string,
    "xp_enabled": boolean,
    "modlog_channel": integer | null,
    "autorole_enabled": boolean,
    "autorole_id": integer | null
  }
}
```

**Example:**
```json
{
  "987654321098765432": {
    "prefix": "!",
    "xp_enabled": true,
    "modlog_channel": 1122334455667788,
    "autorole_enabled": true,
    "autorole_id": 1234567890123456
  },
  "111222333444555666": {
    "prefix": "?",
    "xp_enabled": false,
    "modlog_channel": null,
    "autorole_enabled": false,
    "autorole_id": null
  }
}
```

**Notes:**
- `prefix`: Command prefix for legacy commands (default: `"!"`)
- `xp_enabled`: Whether XP gain from messages is active (default: `true`)
- `modlog_channel`: Channel ID for moderation logs, or `null` if disabled
- `autorole_enabled`: Whether to auto-assign roles to new members
- `autorole_id`: Role ID to assign, or `null` if not configured
- Managed by `cogs/settings.py`
- Defaults are created automatically when a guild first uses settings commands

### `data/warns.json`

Stores moderation warnings per guild and user.

**Schema:**
```json
{
  "guild_id_string": {
    "user_id_string": [
      {
        "reason": string,
        "issued_by": string,
        "timestamp": string (ISO 8601 format)
      }
    ]
  }
}
```

**Example:**
```json
{
  "987654321098765432": {
    "123456789012345678": [
      {
        "reason": "Spamming in general",
        "issued_by": "89161521543811072",
        "timestamp": "2025-12-15T14:32:10.123456"
      },
      {
        "reason": "Inappropriate language",
        "issued_by": "89161521543811072",
        "timestamp": "2025-12-15T16:45:22.654321"
      }
    ]
  }
}
```

**Notes:**
- Each user can have multiple warnings (array)
- `reason`: Text description of the warning
- `issued_by`: User ID (as string) of the moderator who issued the warning
- `timestamp`: UTC timestamp in ISO 8601 format
- Managed by `cogs/moderation.py`
- Warnings can be cleared with `/clear_warns` command

## Migration Notes

When adding new fields or changing schemas:

1. **Backward compatibility**: Ensure old data files still work
2. **Default values**: Handle missing keys gracefully with defaults
3. **Document changes**: Update this file with migration steps
4. **Version migrations**: Consider a migration script for breaking changes
5. **Test**: Validate with existing production data before deploying

## Data Loss Prevention

- **Never edit data files manually** while the bot is running
- **Backup before updates**: Copy `data/` before deploying new versions
- **Validate after edits**: Run `python3 validate_bot.py` after any manual changes
- **Git ignore**: Ensure `data/` is in `.gitignore` to prevent accidental commits
