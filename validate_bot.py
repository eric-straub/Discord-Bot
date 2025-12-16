#!/usr/bin/env python3
"""
Pre-flight bot validation script.
Run before starting the bot to catch common issues early.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

class BotValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = 0
        
    def check(self, condition, message, is_error=True):
        """Record result of a check."""
        if condition:
            self.passed += 1
            print(f"✅ {message}")
        else:
            if is_error:
                self.errors.append(message)
                print(f"❌ {message}")
            else:
                self.warnings.append(message)
                print(f"⚠️  {message}")
    
    def print_summary(self):
        """Print final summary."""
        print("\n" + "="*60)
        print(f"Results: {self.passed} checks passed")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   - {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        print("="*60 + "\n")
        
        if self.errors:
            print("🛑 Fix errors before running the bot!")
            return False
        elif self.warnings:
            print("⚠️  Warnings found - review before running")
            return True
        else:
            print("✅ All checks passed! Bot is ready to run.")
            return True

def main():
    print("🤖 Discord Bot - Pre-Flight Validator\n")
    validator = BotValidator()
    
    # ===== Environment Checks =====
    print("📋 Checking environment...")
    
    env_path = Path(".env")
    validator.check(
        env_path.exists(),
        ".env file exists"
    )
    
    if env_path.exists():
        with open(env_path) as f:
            env_content = f.read()
        validator.check(
            "DISCORD_TOKEN=" in env_content,
            ".env contains DISCORD_TOKEN"
        )
        validator.check(
            "APPLICATION_ID=" in env_content,
            ".env contains APPLICATION_ID"
        )
        validator.check(
            "ADMIN_IDS=" in env_content,
            ".env contains ADMIN_IDS (comma-separated user IDs for admin commands)",
            is_error=False
        )
    
    # ===== File Structure Checks =====
    print("\n📂 Checking file structure...")
    
    required_files = [
        "bot.py",
        "requirements.txt",
        "README.md",
    ]
    
    for file in required_files:
        validator.check(
            Path(file).exists(),
            f"Required file exists: {file}"
        )
    
    required_cogs = [
        "cogs/general.py",
        "cogs/rank.py",
        "cogs/fun.py",
        "cogs/moderation.py",
        "cogs/economy.py",
        "cogs/settings.py",
        "cogs/trivia.py",
        "cogs/casino.py",
    ]
    
    for cog in required_cogs:
        validator.check(
            Path(cog).exists(),
            f"Cog exists: {cog}"
        )
    
    # ===== Python Syntax Checks =====
    print("\n🐍 Checking Python syntax...")
    
    bot_syntax_ok = True
    try:
        subprocess.run(
            ["python3", "-m", "py_compile", "bot.py"],
            capture_output=True,
            check=True,
            timeout=5
        )
        validator.check(True, "bot.py has valid syntax")
    except Exception as e:
        validator.check(False, f"bot.py syntax error: {e}")
        bot_syntax_ok = False
    
    cogs_syntax_ok = True
    for cog in required_cogs:
        try:
            subprocess.run(
                ["python3", "-m", "py_compile", cog],
                capture_output=True,
                check=True,
                timeout=5
            )
        except Exception:
            validator.check(False, f"{cog} has syntax errors")
            cogs_syntax_ok = False
    
    if cogs_syntax_ok:
        validator.check(True, "All cogs have valid syntax")
    
    # ===== Import Checks =====
    print("\n📦 Checking dependencies...")
    
    try:
        import discord
        validator.check(True, f"discord.py installed (v{discord.__version__})")
    except ImportError:
        validator.check(False, "discord.py not installed - run: pip install discord.py")
    
    try:
        import dotenv
        validator.check(True, "python-dotenv installed")
    except ImportError:
        validator.check(False, "python-dotenv not installed - run: pip install python-dotenv")
    
    # ===== Data Directory Check =====
    print("\n💾 Checking data directory...")
    
    data_dir = Path("data")
    validator.check(
        data_dir.exists(),
        "data/ directory exists (or will be created)"
    )
    
    # Check for existing data files
    data_files = [
        "data/ranks.json",
        "data/economy.json",
        "data/warns.json",
        "data/settings.json",
    ]
    
    for data_file in data_files:
        if Path(data_file).exists():
            try:
                with open(data_file) as f:
                    json.load(f)
                validator.check(True, f"{data_file} is valid JSON")
            except json.JSONDecodeError:
                validator.check(False, f"{data_file} has invalid JSON - delete and restart")
        else:
            validator.check(True, f"{data_file} (will be created on first use)", is_error=False)
    
    # ===== Git Check =====
    print("\n🔐 Checking security...")
    
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        with open(gitignore_path) as f:
            gitignore = f.read()
        validator.check(
            ".env" in gitignore,
            ".env is in .gitignore"
        )
        validator.check(
            "data/" in gitignore,
            "data/ is in .gitignore"
        )
    else:
        validator.check(False, ".gitignore not found - sensitive files may leak to git!")
    
    # ===== Final Checks =====
    print("\n✨ Running final checks...")
    
    validator.check(
        bot_syntax_ok and cogs_syntax_ok,
        "All Python files compile successfully"
    )
    
    validator.check(
        env_path.exists() and "DISCORD_TOKEN=" in open(env_path).read(),
        "Ready to authenticate with Discord"
    )
    
    # ===== Summary =====
    success = validator.print_summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
