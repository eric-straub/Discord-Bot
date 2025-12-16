"""Interactive games cog — Pong, Snake, and Conway's Game of Life."""

import asyncio
import random
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands


class Games(commands.Cog):
    """Interactive games like Pong, Snake, and Conway's Game of Life."""

    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # user_id -> game state

    # ==================== PONG ====================
    
    class PongGame:
        """Simple Pong game state."""
        
        def __init__(self):
            self.width = 20
            self.height = 10
            self.paddle_left = self.height // 2
            self.paddle_right = self.height // 2
            self.ball_x = self.width // 2
            self.ball_y = self.height // 2
            self.ball_dx = random.choice([-1, 1])
            self.ball_dy = random.choice([-1, 1])
            self.score_left = 0
            self.score_right = 0
            self.running = True
            
        def move_paddle(self, is_left: bool, direction: int):
            """Move paddle up (-1) or down (1)."""
            if is_left:
                self.paddle_left = max(0, min(self.height - 1, self.paddle_left + direction))
            else:
                self.paddle_right = max(0, min(self.height - 1, self.paddle_right + direction))
        
        def update(self):
            """Update ball position and check collisions."""
            # Move ball
            self.ball_x += self.ball_dx
            self.ball_y += self.ball_dy
            
            # Top/bottom wall collision
            if self.ball_y <= 0 or self.ball_y >= self.height - 1:
                self.ball_dy *= -1
                self.ball_y = max(0, min(self.height - 1, self.ball_y))
            
            # Left paddle collision
            if self.ball_x <= 1 and abs(self.ball_y - self.paddle_left) <= 1:
                self.ball_dx = 1
                self.ball_x = 1
            
            # Right paddle collision
            if self.ball_x >= self.width - 2 and abs(self.ball_y - self.paddle_right) <= 1:
                self.ball_dx = -1
                self.ball_x = self.width - 2
            
            # Score
            if self.ball_x < 0:
                self.score_right += 1
                self.reset_ball()
            elif self.ball_x >= self.width:
                self.score_left += 1
                self.reset_ball()
        
        def reset_ball(self):
            """Reset ball to center."""
            self.ball_x = self.width // 2
            self.ball_y = self.height // 2
            self.ball_dx = random.choice([-1, 1])
            self.ball_dy = random.choice([-1, 1])
        
        def render(self):
            """Render the game as a string."""
            lines = []
            for y in range(self.height):
                line = ""
                for x in range(self.width):
                    # Ball
                    if x == self.ball_x and y == self.ball_y:
                        line += "⚪"
                    # Left paddle
                    elif x == 0 and abs(y - self.paddle_left) <= 1:
                        line += "🟦"
                    # Right paddle
                    elif x == self.width - 1 and abs(y - self.paddle_right) <= 1:
                        line += "🟥"
                    # Empty space
                    else:
                        line += "⬛"
                lines.append(line)
            
            return f"**PONG** — Score: {self.score_left} : {self.score_right}\n" + "\n".join(lines)

    @app_commands.command(name="pong", description="Play a game of Pong")
    async def pong(self, interaction: discord.Interaction):
        """Start an interactive Pong game."""
        user_id = interaction.user.id
        
        if user_id in self.active_games:
            await interaction.response.send_message("You already have an active game! Finish it first.", ephemeral=True)
            return
        
        game = self.PongGame()
        self.active_games[user_id] = ("pong", game)
        
        # Create view with buttons
        view = PongView(self, user_id, game)
        await interaction.response.send_message(game.render(), view=view)
        view.message = await interaction.original_response()

    # ==================== SNAKE ====================
    
    class SnakeGame:
        """Snake game state."""
        
        def __init__(self):
            self.width = 15
            self.height = 10
            self.snake = [(self.width // 2, self.height // 2)]
            self.direction = (1, 0)  # Right
            self.food = self.spawn_food()
            self.score = 0
            self.game_over = False
        
        def spawn_food(self):
            """Spawn food at random location not on snake."""
            while True:
                food = (random.randint(0, self.width - 1), random.randint(0, self.height - 1))
                if food not in self.snake:
                    return food
        
        def set_direction(self, direction: tuple):
            """Set snake direction (no reversing)."""
            # Prevent reversing
            if (direction[0] + self.direction[0], direction[1] + self.direction[1]) != (0, 0):
                self.direction = direction
        
        def update(self):
            """Move snake and check collisions."""
            if self.game_over:
                return
            
            # Calculate new head position
            head = self.snake[0]
            new_head = (head[0] + self.direction[0], head[1] + self.direction[1])
            
            # Check wall collision
            if (new_head[0] < 0 or new_head[0] >= self.width or 
                new_head[1] < 0 or new_head[1] >= self.height):
                self.game_over = True
                return
            
            # Check self collision
            if new_head in self.snake:
                self.game_over = True
                return
            
            # Move snake
            self.snake.insert(0, new_head)
            
            # Check food
            if new_head == self.food:
                self.score += 1
                self.food = self.spawn_food()
            else:
                self.snake.pop()
        
        def render(self):
            """Render the game as a string."""
            lines = []
            for y in range(self.height):
                line = ""
                for x in range(self.width):
                    pos = (x, y)
                    if pos == self.snake[0]:
                        line += "🟢"  # Head
                    elif pos in self.snake:
                        line += "🟩"  # Body
                    elif pos == self.food:
                        line += "🍎"  # Food
                    else:
                        line += "⬛"
                lines.append(line)
            
            status = "GAME OVER!" if self.game_over else "Playing"
            return f"**SNAKE** — Score: {self.score} | {status}\n" + "\n".join(lines)

    @app_commands.command(name="snake", description="Play Snake game")
    async def snake(self, interaction: discord.Interaction):
        """Start an interactive Snake game."""
        user_id = interaction.user.id
        
        if user_id in self.active_games:
            await interaction.response.send_message("You already have an active game! Finish it first.", ephemeral=True)
            return
        
        game = self.SnakeGame()
        self.active_games[user_id] = ("snake", game)
        
        view = SnakeView(self, user_id, game)
        await interaction.response.send_message(game.render(), view=view)
        view.message = await interaction.original_response()

    # ==================== CONWAY'S GAME OF LIFE ====================
    
    class GameOfLife:
        """Conway's Game of Life state."""
        
        def __init__(self, width=20, height=10):
            self.width = width
            self.height = height
            self.grid = [[False for _ in range(width)] for _ in range(height)]
            self.generation = 0
            self.running = False
        
        def randomize(self, density=0.3):
            """Fill grid with random cells."""
            for y in range(self.height):
                for x in range(self.width):
                    self.grid[y][x] = random.random() < density
        
        def toggle_cell(self, x: int, y: int):
            """Toggle a cell at position."""
            if 0 <= x < self.width and 0 <= y < self.height:
                self.grid[y][x] = not self.grid[y][x]
        
        def count_neighbors(self, x: int, y: int) -> int:
            """Count living neighbors around a cell."""
            count = 0
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if self.grid[ny][nx]:
                            count += 1
            return count
        
        def step(self):
            """Advance one generation."""
            new_grid = [[False for _ in range(self.width)] for _ in range(self.height)]
            
            for y in range(self.height):
                for x in range(self.width):
                    neighbors = self.count_neighbors(x, y)
                    
                    # Conway's rules
                    if self.grid[y][x]:  # Cell is alive
                        new_grid[y][x] = neighbors in [2, 3]
                    else:  # Cell is dead
                        new_grid[y][x] = neighbors == 3
            
            self.grid = new_grid
            self.generation += 1
        
        def clear(self):
            """Clear the grid."""
            self.grid = [[False for _ in range(self.width)] for _ in range(self.height)]
            self.generation = 0
        
        def render(self):
            """Render the grid as a string."""
            lines = []
            for y in range(self.height):
                line = ""
                for x in range(self.width):
                    line += "⬜" if self.grid[y][x] else "⬛"
                lines.append(line)
            
            alive = sum(sum(row) for row in self.grid)
            return f"**Conway's Game of Life** — Generation: {self.generation} | Alive: {alive}\n" + "\n".join(lines)

    @app_commands.command(name="gameoflife", description="Conway's Game of Life simulator")
    async def gameoflife(self, interaction: discord.Interaction):
        """Start Conway's Game of Life simulator."""
        user_id = interaction.user.id
        
        if user_id in self.active_games:
            await interaction.response.send_message("You already have an active game! Finish it first.", ephemeral=True)
            return
        
        game = self.GameOfLife()
        game.randomize()
        self.active_games[user_id] = ("gameoflife", game)
        
        view = GameOfLifeView(self, user_id, game)
        await interaction.response.send_message(game.render(), view=view)
        view.message = await interaction.original_response()


# ==================== VIEWS (BUTTON CONTROLS) ====================

class PongView(discord.ui.View):
    def __init__(self, cog, user_id, game):
        super().__init__(timeout=180)
        self.cog = cog
        self.user_id = user_id
        self.game = game
        self.message = None
        self.auto_play_task = None
        self.start_auto_play()
    
    def start_auto_play(self):
        """Start automatic game updates."""
        self.auto_play_task = asyncio.create_task(self.auto_play_loop())
    
    async def auto_play_loop(self):
        """Auto-update game every 0.5 seconds."""
        try:
            while self.game.running:
                await asyncio.sleep(0.5)
                self.game.update()
                if self.message:
                    try:
                        await self.message.edit(content=self.game.render(), view=self)
                    except:
                        break
        except asyncio.CancelledError:
            pass
    
    @discord.ui.button(label="↑ Left", style=discord.ButtonStyle.primary, row=0)
    async def left_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.game.move_paddle(True, -1)
        await interaction.response.defer()
    
    @discord.ui.button(label="↓ Left", style=discord.ButtonStyle.primary, row=0)
    async def left_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.game.move_paddle(True, 1)
        await interaction.response.defer()
    
    @discord.ui.button(label="↑ Right", style=discord.ButtonStyle.danger, row=0)
    async def right_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.game.move_paddle(False, -1)
        await interaction.response.defer()
    
    @discord.ui.button(label="↓ Right", style=discord.ButtonStyle.danger, row=0)
    async def right_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.game.move_paddle(False, 1)
        await interaction.response.defer()
    
    @discord.ui.button(label="Quit", style=discord.ButtonStyle.secondary, row=1)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.game.running = False
        if self.auto_play_task:
            self.auto_play_task.cancel()
        self.cog.active_games.pop(self.user_id, None)
        await interaction.response.edit_message(content=f"{self.game.render()}\n**Game Over!**", view=None)
        self.stop()


class SnakeView(discord.ui.View):
    def __init__(self, cog, user_id, game):
        super().__init__(timeout=180)
        self.cog = cog
        self.user_id = user_id
        self.game = game
        self.message = None
        self.auto_move_task = None
        self.start_auto_move()
    
    def start_auto_move(self):
        """Start automatic snake movement."""
        self.auto_move_task = asyncio.create_task(self.auto_move_loop())
    
    async def auto_move_loop(self):
        """Auto-move snake every 0.8 seconds."""
        try:
            while not self.game.game_over:
                await asyncio.sleep(0.8)
                self.game.update()
                if self.message:
                    try:
                        if self.game.game_over:
                            await self.message.edit(content=self.game.render(), view=None)
                            self.cog.active_games.pop(self.user_id, None)
                            self.stop()
                        else:
                            await self.message.edit(content=self.game.render(), view=self)
                    except:
                        break
        except asyncio.CancelledError:
            pass
    
    @discord.ui.button(emoji="⬆️", style=discord.ButtonStyle.primary, row=0)
    async def up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.game.set_direction((0, -1))
        await interaction.response.defer()
    
    @discord.ui.button(emoji="⬇️", style=discord.ButtonStyle.primary, row=1)
    async def down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.game.set_direction((0, 1))
        await interaction.response.defer()
    
    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.primary, row=1)
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.game.set_direction((-1, 0))
        await interaction.response.defer()
    
    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.primary, row=1)
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.game.set_direction((1, 0))
        await interaction.response.defer()
    
    @discord.ui.button(label="Quit", style=discord.ButtonStyle.danger, row=2)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        if self.auto_move_task:
            self.auto_move_task.cancel()
        self.cog.active_games.pop(self.user_id, None)
        await interaction.response.edit_message(content=f"{self.game.render()}\n**Quit!**", view=None)
        self.stop()


class GameOfLifeView(discord.ui.View):
    def __init__(self, cog, user_id, game):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.game = game
        self.message = None
    
    @discord.ui.button(label="Step", style=discord.ButtonStyle.primary, row=0)
    async def step(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.game.step()
        await interaction.response.edit_message(content=self.game.render(), view=self)
    
    @discord.ui.button(label="Auto (10x)", style=discord.ButtonStyle.success, row=0)
    async def auto_step(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        await interaction.response.defer()
        for _ in range(10):
            self.game.step()
            await asyncio.sleep(0.3)
            try:
                await interaction.edit_original_response(content=self.game.render(), view=self)
            except:
                break
    
    @discord.ui.button(label="Randomize", style=discord.ButtonStyle.secondary, row=0)
    async def randomize(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.game.randomize()
        await interaction.response.edit_message(content=self.game.render(), view=self)
    
    @discord.ui.button(label="Clear", style=discord.ButtonStyle.secondary, row=0)
    async def clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.game.clear()
        await interaction.response.edit_message(content=self.game.render(), view=self)
    
    @discord.ui.button(label="Quit", style=discord.ButtonStyle.danger, row=1)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.cog.active_games.pop(self.user_id, None)
        await interaction.response.edit_message(content=f"{self.game.render()}\n**Session ended!**", view=None)
        self.stop()


async def setup(bot):
    await bot.add_cog(Games(bot))
