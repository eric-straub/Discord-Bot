# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.0.2-alpha] - 2025-12-18

### Added
- Echo command (prefix and slash variants)
- Git commit/timestamp information in `/version`
- Persistent cooldown storage for fun and trivia commands

### Changed
- Added per-user cooldowns to fun and trivia commands
- Migrated `data/ranks.json` and `data/economy.json` to a new data schema
- Major casino code refactor consolidating game logic

### Removed
- Moderation cog (warnings, kick, ban, timeout, purge commands)
- Settings cog (per-guild configuration system)
- Casino mini-games: coinflip, dice, and crash

## [0.0.1-alpha] - 2025-12-15

### Added
- Initial alpha release
- General commands (ping, hello, echo, version, server_stats, help)
- Rank system with XP/level tracking and leaderboards
- Economy system with currency, daily rewards, and transfers
- Trivia system with spoiler-based answers and fuzzy matching
- Casino games (blackjack, slots, roulette, coinflip, dice, crash)
- Fun commands (dice rolls, coin flip, 8ball, rock-paper-scissors)
- Interactive games (Pong, Snake, Conway's Game of Life)
- Dual command support (slash and prefix commands)
- JSON-based data persistence
- Pre-flight validation script (`validate_bot.py`)
- Gateway event logging for debugging
- Autorole assignment on member join
- Cross-cog communication patterns
