# Contributing

Thanks for your interest in contributing to this Discord bot project! This document describes the recommended workflow, coding conventions, and the PR checklist to make contributions smooth.

## Getting Started

1. Fork the repository and create a feature branch off `dev`:

```bash
git checkout -b feature/your-feature dev
```

2. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

3. Run the validator before making code changes and before opening a PR:

```bash
python3 validate_bot.py
```

## Coding Guidelines

- Use `discord.py` idioms: prefer `app_commands` for slash commands and `commands.Cog` for cogs.
- Keep functions small and focused. Avoid global mutable state outside `data/` storage.
- If you change runtime data formats (JSON structure), update `docs/data-format.md` and include migration notes in your PR.
- Use type hints where useful but don’t over-annotate trivial code.

## Adding a New Cog

1. Add a new file to `cogs/` — follow existing files as examples.
2. Define a `class MyCog(commands.Cog)` and export an `async def setup(bot)` that calls `await bot.add_cog(MyCog(bot))`.
3. Register the cog in `MyBot.setup_hook()` inside `bot.py`:

```py
await self.load_extension("cogs.yourcog")
```

4. Add syntax checks:

```bash
python3 -m py_compile cogs/yourcog.py
```

5. Run `python3 validate_bot.py`.

## Tests & Validation

- There are no unit tests included by default. If you add testable logic, include tests and document how to run them.
- Always run `validate_bot.py` before opening a PR to catch obvious issues.

## Pull Request Checklist

- [ ] Branched from `dev` and targeted at `dev`.
- [ ] Ran `python3 validate_bot.py` and fixed reported issues.
- [ ] Added documentation updates for any new user-visible features or data format changes.
- [ ] Small, focused commits with clear messages.
- [ ] Describe any manual migration or setup steps in the PR description.

## Communication

If your change is large or impacts others, open an issue first to discuss the design.
