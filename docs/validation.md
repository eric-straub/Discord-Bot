# Validator (`validate_bot.py`)

The `validate_bot.py` script is a comprehensive pre-flight checker that detects common configuration, syntax, and setup issues before launching the bot. Running this before deployment helps catch problems early and ensures a smooth bot startup.

## What It Checks

### 1. Environment Configuration
- ✅ `.env` file exists in the project root
- ✅ `DISCORD_TOKEN` is present (required for authentication)
- ✅ `APPLICATION_ID` is present (required for slash commands)
- ⚠️  `ADMIN_IDS` is present (optional, warns if missing)

### 2. File Structure
- ✅ Required files exist: `bot.py`, `requirements.txt`, `README.md`
- ✅ All cogs referenced in `bot.py` have corresponding files:
  - `cogs/general.py`
  - `cogs/rank.py`
  - `cogs/fun.py`
  - `cogs/moderation.py`
  - `cogs/economy.py`
  - `cogs/settings.py`
  - `cogs/trivia.py`
  - `cogs/casino.py`

### 3. Python Syntax
- ✅ `bot.py` compiles without syntax errors
- ✅ All cog files compile without syntax errors
- Uses `python -m py_compile` for validation

### 4. Dependencies
- ✅ `discord.py` is installed (reports version)
- ✅ `python-dotenv` is installed

### 5. Data Directory
- ✅ `data/` directory exists (or will be created)
- ✅ Existing JSON files are valid JSON:
  - `data/ranks.json`
  - `data/economy.json`
  - `data/warns.json`
  - `data/settings.json`
- ℹ️  Missing data files are noted (not errors - auto-created on first use)

### 6. Security
- ✅ `.gitignore` contains `.env` entry (prevents token leaks)
- ✅ `.gitignore` contains `data/` entry (prevents data commits)

### 7. Final Readiness
- ✅ All Python files compile successfully
- ✅ Bot is ready to authenticate with Discord

## How to Run

```bash
python3 validate_bot.py
```

**Before running:**
- Ensure you're in the project root directory
- Have Python 3.10+ installed
- Have installed dependencies (`pip install -r requirements.txt`)

## Understanding Output

### Success Indicators
```
✅ .env file exists
✅ .env contains DISCORD_TOKEN
✅ discord.py installed (v2.3.2)
✅ All checks passed! Bot is ready to run.
```

### Warnings
```
⚠️  .env contains ADMIN_IDS (comma-separated user IDs for admin commands)
⚠️  data/economy.json (will be created on first use)
```

Warnings don't prevent the bot from running but should be reviewed.

### Errors
```
❌ .env file exists
❌ cogs/trivia.py has syntax errors
❌ data/ranks.json has invalid JSON - delete and restart
🛑 Fix errors before running the bot!
```

Errors must be fixed before the bot can run properly.

## Exit Codes

- **0** - All checks passed (or only warnings present)
- **1** - Critical errors found that must be fixed

Use in CI/CD:
```bash
python3 validate_bot.py && python3 bot.py
```

## Common Issues & Fixes

### Missing .env file
```
❌ .env file exists
```

**Fix:** Create a `.env` file in the project root:
```bash
touch .env
```

Then add your bot credentials (see README.md).

### Syntax Errors
```
❌ cogs/economy.py has syntax errors
```

**Fix:** Check the file for Python syntax issues:
```bash
python3 -m py_compile cogs/economy.py
```

The error message will show the line number and issue.

### Invalid JSON
```
❌ data/ranks.json has invalid JSON - delete and restart
```

**Fix:** Either correct the JSON manually or delete the file:
```bash
rm data/ranks.json
```

The bot will recreate it with valid JSON on next use.

### Missing Dependencies
```
❌ discord.py not installed - run: pip install discord.py
```

**Fix:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Git Security Issues
```
❌ .env is in .gitignore
```

**Fix:** Add to `.gitignore`:
```
.env
data/
__pycache__/
*.pyc
```

## Extending the Validator

When adding new features, update the validator to check them:

### Adding a New Cog

Edit `validate_bot.py`:
```python
required_cogs = [
    "cogs/general.py",
    # ... existing cogs
    "cogs/yourcog.py",  # Add your cog
]
```

### Adding a New Data File

Edit `validate_bot.py`:
```python
data_files = [
    "data/ranks.json",
    # ... existing files
    "data/yourdata.json",  # Add your data file
]
```

### Adding Custom Checks

Add a new validation section:
```python
print("\n🔍 Checking custom requirements...")

validator.check(
    some_condition,
    "Description of what you're checking"
)
```

## Integration with Development Workflow

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
python3 validate_bot.py
if [ $? -ne 0 ]; then
    echo "❌ Validation failed! Fix issues before committing."
    exit 1
fi
```

### CI/CD Pipeline
GitHub Actions example (`.github/workflows/validate.yml`):
```yaml
name: Validate Bot
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python3 validate_bot.py
```

### VS Code Tasks
Add to `.vscode/tasks.json`:
```json
{
  "label": "Validate Bot",
  "type": "shell",
  "command": "python3 validate_bot.py",
  "problemMatcher": []
}
```

## Best Practices

1. **Run before every deployment** - Catch issues before production
2. **Run after adding cogs** - Ensure new code is syntactically valid
3. **Run after editing data files** - Verify JSON is still valid
4. **Include in CI/CD** - Automate validation on every commit
5. **Keep validator updated** - Add checks for new features
6. **Don't skip warnings** - Review and address them when possible
