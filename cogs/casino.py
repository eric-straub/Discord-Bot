"""Casino cog — gambling games like blackjack where users can bet credits."""

import random
import asyncio

import discord
from discord.ext import commands
from discord import app_commands


class Casino(commands.Cog):
    """Casino games for betting credits."""

    def __init__(self, bot):
        self.bot = bot
        # active_games: user_id -> game state dict
        self.active_games = {}

    def _create_deck(self):
        """Create a standard 52-card deck."""
        suits = ['♠️', '♥️', '♦️', '♣️']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [{'rank': rank, 'suit': suit} for suit in suits for rank in ranks]
        random.shuffle(deck)
        return deck

    def _card_value(self, card):
        """Return numeric value of a card for blackjack."""
        rank = card['rank']
        if rank in ['J', 'Q', 'K']:
            return 10
        elif rank == 'A':
            return 11  # Aces are 11 by default, adjusted later if needed
        else:
            return int(rank)

    def _calculate_hand_value(self, hand):
        """Calculate the total value of a hand, adjusting for aces."""
        value = sum(self._card_value(card) for card in hand)
        aces = sum(1 for card in hand if card['rank'] == 'A')
        
        # Adjust for aces if bust
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value

    def _format_hand(self, hand, hide_first=False):
        """Format a hand for display."""
        if hide_first:
            cards = ['🂠'] + [f"{card['rank']}{card['suit']}" for card in hand[1:]]
        else:
            cards = [f"{card['rank']}{card['suit']}" for card in hand]
        return ' '.join(cards)

    def _get_game_embed(self, game, user, final=False):
        """Create an embed showing the current game state."""
        embed = discord.Embed(title="🎰 Blackjack", color=discord.Color.gold())
        
        dealer_hand = self._format_hand(game['dealer_hand'], hide_first=not final)
        player_hand = self._format_hand(game['player_hand'])
        
        player_value = self._calculate_hand_value(game['player_hand'])
        
        embed.add_field(
            name="Dealer's Hand" + (f" ({self._calculate_hand_value(game['dealer_hand'])})" if final else ""),
            value=dealer_hand,
            inline=False
        )
        embed.add_field(
            name=f"{user.display_name}'s Hand ({player_value})",
            value=player_hand,
            inline=False
        )
        embed.add_field(name="Bet", value=f"🪙 {game['bet']} credits", inline=True)
        
        return embed

    @app_commands.command(name="blackjack", description="Play blackjack and bet your credits")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        """Start a game of blackjack with a specified bet amount."""
        await interaction.response.defer()

        user_id = interaction.user.id

        # Check if user already has an active game
        if user_id in self.active_games:
            await interaction.followup.send("You already have an active blackjack game! Finish it first.", ephemeral=True)
            return

        # Validate bet amount
        if bet <= 0:
            await interaction.followup.send("Bet must be greater than 0.", ephemeral=True)
            return

        # Check if user has enough credits
        econ_cog = self.bot.get_cog('Economy')
        if not econ_cog:
            await interaction.followup.send("Economy system not available.", ephemeral=True)
            return

        econ_cog._ensure_user(user_id)
        user_balance = econ_cog.economy[str(user_id)]['balance']

        if user_balance < bet:
            await interaction.followup.send(f"You don't have enough credits! Your balance: 🪙 {user_balance}", ephemeral=True)
            return

        # Deduct bet from balance
        if not econ_cog._remove_balance(user_id, bet):
            await interaction.followup.send("Failed to place bet.", ephemeral=True)
            return

        # Initialize game
        deck = self._create_deck()
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        game = {
            'deck': deck,
            'player_hand': player_hand,
            'dealer_hand': dealer_hand,
            'bet': bet,
            'channel_id': interaction.channel_id
        }

        self.active_games[user_id] = game

        # Check for natural blackjack
        player_value = self._calculate_hand_value(player_hand)
        dealer_value = self._calculate_hand_value(dealer_hand)

        if player_value == 21:
            # Player has blackjack
            if dealer_value == 21:
                # Push
                econ_cog._add_balance(user_id, bet)
                embed = self._get_game_embed(game, interaction.user, final=True)
                embed.add_field(name="Result", value="🤝 Push! Both have blackjack. Bet returned.", inline=False)
            else:
                # Player wins with blackjack (pays 3:2)
                winnings = int(bet * 2.5)
                econ_cog._add_balance(user_id, winnings)
                embed = self._get_game_embed(game, interaction.user, final=True)
                embed.add_field(name="Result", value=f"🎉 Blackjack! You win 🪙 {winnings - bet} credits!", inline=False)
            
            del self.active_games[user_id]
            await interaction.followup.send(embed=embed)
            return

        # Regular game - show initial state with buttons
        embed = self._get_game_embed(game, interaction.user)
        
        view = BlackjackView(self, interaction.user)
        await interaction.followup.send(embed=embed, view=view)

    async def hit(self, interaction: discord.Interaction):
        """Player draws another card."""
        user_id = interaction.user.id
        game = self.active_games.get(user_id)

        if not game:
            await interaction.response.send_message("No active game found.", ephemeral=True)
            return

        # Draw a card
        game['player_hand'].append(game['deck'].pop())
        player_value = self._calculate_hand_value(game['player_hand'])

        if player_value > 21:
            # Bust
            embed = self._get_game_embed(game, interaction.user, final=True)
            embed.add_field(name="Result", value=f"💥 Bust! You lose 🪙 {game['bet']} credits.", inline=False)
            del self.active_games[user_id]
            await interaction.response.edit_message(embed=embed, view=None)
        elif player_value == 21:
            # Auto-stand on 21
            await self.stand(interaction)
        else:
            # Continue game
            embed = self._get_game_embed(game, interaction.user)
            view = BlackjackView(self, interaction.user)
            await interaction.response.edit_message(embed=embed, view=view)

    async def stand(self, interaction: discord.Interaction):
        """Player stands - dealer plays and game resolves."""
        user_id = interaction.user.id
        game = self.active_games.get(user_id)

        if not game:
            await interaction.response.send_message("No active game found.", ephemeral=True)
            return

        # Dealer plays - must hit on 16 or less, stand on 17 or more
        while self._calculate_hand_value(game['dealer_hand']) < 17:
            game['dealer_hand'].append(game['deck'].pop())

        player_value = self._calculate_hand_value(game['player_hand'])
        dealer_value = self._calculate_hand_value(game['dealer_hand'])

        econ_cog = self.bot.get_cog('Economy')
        embed = self._get_game_embed(game, interaction.user, final=True)

        if dealer_value > 21:
            # Dealer bust - player wins
            winnings = game['bet'] * 2
            econ_cog._add_balance(user_id, winnings)
            embed.add_field(name="Result", value=f"🎉 Dealer busts! You win 🪙 {game['bet']} credits!", inline=False)
        elif player_value > dealer_value:
            # Player wins
            winnings = game['bet'] * 2
            econ_cog._add_balance(user_id, winnings)
            embed.add_field(name="Result", value=f"🎉 You win 🪙 {game['bet']} credits!", inline=False)
        elif player_value < dealer_value:
            # Dealer wins
            embed.add_field(name="Result", value=f"😢 Dealer wins. You lose 🪙 {game['bet']} credits.", inline=False)
        else:
            # Push
            econ_cog._add_balance(user_id, game['bet'])
            embed.add_field(name="Result", value="🤝 Push! Bet returned.", inline=False)

        del self.active_games[user_id]
        await interaction.response.edit_message(embed=embed, view=None)


class BlackjackView(discord.ui.View):
    """View with Hit and Stand buttons for blackjack."""

    def __init__(self, casino_cog, user):
        super().__init__(timeout=120)  # 2 minute timeout
        self.casino_cog = casino_cog
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the game owner to use buttons."""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary, emoji="🎴")
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.casino_cog.hit(interaction)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary, emoji="✋")
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.casino_cog.stand(interaction)

    async def on_timeout(self):
        """Handle timeout - auto-stand."""
        game = self.casino_cog.active_games.get(self.user.id)
        if game:
            # Clean up abandoned game - return bet
            econ_cog = self.casino_cog.bot.get_cog('Economy')
            if econ_cog:
                econ_cog._add_balance(self.user.id, game['bet'])
            del self.casino_cog.active_games[self.user.id]


    # ========== SLOTS ==========

    @app_commands.command(name="slots", description="Play the slot machine (min bet: 10)")
    @app_commands.describe(bet="Amount of credits to bet")
    async def slots(self, interaction: discord.Interaction, bet: int):
        """Spin the slot machine - match symbols to win!"""
        await interaction.response.defer()

        user_id = interaction.user.id
        
        if bet < 10:
            await interaction.followup.send("Minimum bet is 🪙 10 credits.", ephemeral=True)
            return

        econ_cog = self.bot.get_cog('Economy')
        if not econ_cog:
            await interaction.followup.send("Economy system is not available.", ephemeral=True)
            return

        econ_cog._ensure_user(user_id)
        user_balance = econ_cog.economy[str(user_id)]['balance']

        if user_balance < bet:
            await interaction.followup.send(f"You don't have enough credits! Your balance: 🪙 {user_balance}", ephemeral=True)
            return

        # Deduct bet
        if not econ_cog._remove_balance(user_id, bet):
            await interaction.followup.send("Failed to place bet.", ephemeral=True)
            return

        # Slot symbols with weighted probabilities
        symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
        weights = [30, 25, 20, 15, 7, 2, 1]  # Higher weight = more common

        # Spin the reels
        reels = [random.choices(symbols, weights=weights, k=1)[0] for _ in range(3)]

        # Calculate winnings
        winnings = 0
        result_text = ""

        if reels[0] == reels[1] == reels[2]:
            # All three match - jackpot!
            multipliers = {'🍒': 5, '🍋': 8, '🍊': 10, '🍇': 15, '🔔': 25, '💎': 50, '7️⃣': 100}
            multiplier = multipliers.get(reels[0], 5)
            winnings = bet * multiplier
            result_text = f"🎰 **JACKPOT!** All {reels[0]}!\nYou win 🪙 **{winnings}** credits! ({multiplier}x)"
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            # Two match - smaller win
            winnings = bet * 2
            result_text = f"🎲 Two matching! You win 🪙 **{winnings}** credits! (2x)"
        else:
            result_text = f"😢 No matches. You lose 🪙 {bet} credits."

        if winnings > 0:
            econ_cog._add_balance(user_id, winnings)

        # Create embed with slot display
        embed = discord.Embed(
            title="🎰 Slot Machine 🎰",
            description=f"**[ {reels[0]} | {reels[1]} | {reels[2]} ]**\n\n{result_text}",
            color=discord.Color.gold() if winnings > 0 else discord.Color.red()
        )
        embed.add_field(name="Bet", value=f"🪙 {bet}", inline=True)
        if winnings > 0:
            embed.add_field(name="Won", value=f"🪙 {winnings - bet}", inline=True)
        embed.set_footer(text=f"Balance: 🪙 {econ_cog.economy[str(user_id)]['balance']}")

        await interaction.followup.send(embed=embed)

    # ========== ROULETTE ==========

    @app_commands.command(name="roulette", description="Bet on roulette (red, black, even, odd, or a number)")
    @app_commands.describe(
        bet="Amount of credits to bet",
        choice="Your bet: 'red', 'black', 'even', 'odd', or a number (0-36)"
    )
    async def roulette(self, interaction: discord.Interaction, bet: int, choice: str):
        """Spin the roulette wheel!"""
        await interaction.response.defer()

        user_id = interaction.user.id
        
        if bet < 10:
            await interaction.followup.send("Minimum bet is 🪙 10 credits.", ephemeral=True)
            return

        econ_cog = self.bot.get_cog('Economy')
        if not econ_cog:
            await interaction.followup.send("Economy system is not available.", ephemeral=True)
            return

        econ_cog._ensure_user(user_id)
        user_balance = econ_cog.economy[str(user_id)]['balance']

        if user_balance < bet:
            await interaction.followup.send(f"You don't have enough credits! Your balance: 🪙 {user_balance}", ephemeral=True)
            return

        # Validate choice
        choice = choice.lower().strip()
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

        is_number_bet = False
        bet_number = None

        if choice.isdigit():
            bet_number = int(choice)
            if 0 <= bet_number <= 36:
                is_number_bet = True
            else:
                await interaction.followup.send("Number must be between 0 and 36.", ephemeral=True)
                return
        elif choice not in ['red', 'black', 'even', 'odd']:
            await interaction.followup.send("Invalid choice. Use: red, black, even, odd, or a number (0-36).", ephemeral=True)
            return

        # Deduct bet
        if not econ_cog._remove_balance(user_id, bet):
            await interaction.followup.send("Failed to place bet.", ephemeral=True)
            return

        # Spin the wheel
        result = random.randint(0, 36)
        is_red = result in red_numbers
        is_black = result in black_numbers
        is_even = result % 2 == 0 and result != 0
        is_odd = result % 2 == 1

        # Determine color emoji
        if result == 0:
            color_emoji = "🟢"
            color_name = "Green"
        elif is_red:
            color_emoji = "🔴"
            color_name = "Red"
        else:
            color_emoji = "⚫"
            color_name = "Black"

        # Check win
        won = False
        multiplier = 0

        if is_number_bet:
            if result == bet_number:
                won = True
                multiplier = 36  # 35:1 payout + original bet
        elif choice == 'red' and is_red:
            won = True
            multiplier = 2
        elif choice == 'black' and is_black:
            won = True
            multiplier = 2
        elif choice == 'even' and is_even:
            won = True
            multiplier = 2
        elif choice == 'odd' and is_odd:
            won = True
            multiplier = 2

        winnings = 0
        if won:
            winnings = bet * multiplier
            econ_cog._add_balance(user_id, winnings)

        # Create result embed
        embed = discord.Embed(
            title="🎡 Roulette Wheel 🎡",
            description=f"**The ball lands on... {color_emoji} {result} {color_emoji}**\n({color_name})",
            color=discord.Color.green() if won else discord.Color.red()
        )
        embed.add_field(name="Your Bet", value=f"{choice.title()} - 🪙 {bet}", inline=True)
        
        if won:
            embed.add_field(name="Result", value=f"🎉 You win 🪙 **{winnings - bet}** credits!", inline=False)
        else:
            embed.add_field(name="Result", value=f"😢 You lose 🪙 {bet} credits.", inline=False)

        embed.set_footer(text=f"Balance: 🪙 {econ_cog.economy[str(user_id)]['balance']}")
        
        await interaction.followup.send(embed=embed)

    # ========== COINFLIP ==========

    @app_commands.command(name="coinflip", description="Flip a coin - double or nothing!")
    @app_commands.describe(
        bet="Amount of credits to bet",
        choice="Your guess: heads or tails"
    )
    async def coinflip(self, interaction: discord.Interaction, bet: int, choice: str):
        """Bet on a coin flip!"""
        await interaction.response.defer()

        user_id = interaction.user.id
        
        if bet < 10:
            await interaction.followup.send("Minimum bet is 🪙 10 credits.", ephemeral=True)
            return

        choice = choice.lower().strip()
        if choice not in ['heads', 'tails', 'h', 't']:
            await interaction.followup.send("Choose 'heads' or 'tails'.", ephemeral=True)
            return

        # Normalize choice
        if choice in ['h', 'heads']:
            choice = 'heads'
        else:
            choice = 'tails'

        econ_cog = self.bot.get_cog('Economy')
        if not econ_cog:
            await interaction.followup.send("Economy system is not available.", ephemeral=True)
            return

        econ_cog._ensure_user(user_id)
        user_balance = econ_cog.economy[str(user_id)]['balance']

        if user_balance < bet:
            await interaction.followup.send(f"You don't have enough credits! Your balance: 🪙 {user_balance}", ephemeral=True)
            return

        # Deduct bet
        if not econ_cog._remove_balance(user_id, bet):
            await interaction.followup.send("Failed to place bet.", ephemeral=True)
            return

        # Flip the coin
        result = random.choice(['heads', 'tails'])
        emoji = "🪙"

        won = (result == choice)
        
        if won:
            winnings = bet * 2
            econ_cog._add_balance(user_id, winnings)

        # Create result embed
        embed = discord.Embed(
            title=f"{emoji} Coin Flip {emoji}",
            description=f"**The coin lands on... {result.upper()}!**",
            color=discord.Color.green() if won else discord.Color.red()
        )
        embed.add_field(name="Your Guess", value=choice.title(), inline=True)
        embed.add_field(name="Bet", value=f"🪙 {bet}", inline=True)
        
        if won:
            embed.add_field(name="Result", value=f"🎉 Correct! You win 🪙 **{bet}** credits!", inline=False)
        else:
            embed.add_field(name="Result", value=f"😢 Wrong! You lose 🪙 {bet} credits.", inline=False)

        embed.set_footer(text=f"Balance: 🪙 {econ_cog.economy[str(user_id)]['balance']}")
        
        await interaction.followup.send(embed=embed)

    # ========== DICE ==========

    @app_commands.command(name="dice", description="Roll 2 dice and bet on the outcome")
    @app_commands.describe(
        bet="Amount of credits to bet",
        choice="Bet on: 'high' (8-12), 'low' (2-6), 'seven' (7), or 'doubles'"
    )
    async def dice(self, interaction: discord.Interaction, bet: int, choice: str):
        """Roll the dice and win!"""
        await interaction.response.defer()

        user_id = interaction.user.id
        
        if bet < 10:
            await interaction.followup.send("Minimum bet is 🪙 10 credits.", ephemeral=True)
            return

        choice = choice.lower().strip()
        valid_choices = ['high', 'low', 'seven', 'doubles']
        if choice not in valid_choices:
            await interaction.followup.send(f"Invalid choice. Choose: {', '.join(valid_choices)}", ephemeral=True)
            return

        econ_cog = self.bot.get_cog('Economy')
        if not econ_cog:
            await interaction.followup.send("Economy system is not available.", ephemeral=True)
            return

        econ_cog._ensure_user(user_id)
        user_balance = econ_cog.economy[str(user_id)]['balance']

        if user_balance < bet:
            await interaction.followup.send(f"You don't have enough credits! Your balance: 🪙 {user_balance}", ephemeral=True)
            return

        # Deduct bet
        if not econ_cog._remove_balance(user_id, bet):
            await interaction.followup.send("Failed to place bet.", ephemeral=True)
            return

        # Roll the dice
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        total = die1 + die2

        # Determine win and multiplier
        won = False
        multiplier = 0

        if choice == 'high' and total >= 8:
            won = True
            multiplier = 2
        elif choice == 'low' and total <= 6:
            won = True
            multiplier = 2
        elif choice == 'seven' and total == 7:
            won = True
            multiplier = 4
        elif choice == 'doubles' and die1 == die2:
            won = True
            multiplier = 6

        winnings = 0
        if won:
            winnings = bet * multiplier
            econ_cog._add_balance(user_id, winnings)

        # Dice emoji mapping
        dice_emoji = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

        # Create result embed
        embed = discord.Embed(
            title="🎲 Dice Roll 🎲",
            description=f"**{dice_emoji[die1]} {dice_emoji[die2]}**\n\nTotal: **{total}**",
            color=discord.Color.green() if won else discord.Color.red()
        )
        embed.add_field(name="Your Bet", value=f"{choice.title()} - 🪙 {bet}", inline=True)
        
        if won:
            embed.add_field(name="Result", value=f"🎉 You win 🪙 **{winnings - bet}** credits! ({multiplier}x)", inline=False)
        else:
            embed.add_field(name="Result", value=f"😢 You lose 🪙 {bet} credits.", inline=False)

        embed.set_footer(text=f"Balance: 🪙 {econ_cog.economy[str(user_id)]['balance']}")
        
        await interaction.followup.send(embed=embed)

    # ========== CRASH ==========

    @app_commands.command(name="crash", description="Multiplier game - cash out before it crashes!")
    @app_commands.describe(bet="Amount of credits to bet")
    async def crash(self, interaction: discord.Interaction, bet: int):
        """Play crash - watch the multiplier rise and cash out before it crashes!"""
        await interaction.response.defer()

        user_id = interaction.user.id
        
        if bet < 10:
            await interaction.followup.send("Minimum bet is 🪙 10 credits.", ephemeral=True)
            return

        if user_id in self.active_games:
            await interaction.followup.send("You already have an active game! Finish it first.", ephemeral=True)
            return

        econ_cog = self.bot.get_cog('Economy')
        if not econ_cog:
            await interaction.followup.send("Economy system is not available.", ephemeral=True)
            return

        econ_cog._ensure_user(user_id)
        user_balance = econ_cog.economy[str(user_id)]['balance']

        if user_balance < bet:
            await interaction.followup.send(f"You don't have enough credits! Your balance: 🪙 {user_balance}", ephemeral=True)
            return

        # Deduct bet
        if not econ_cog._remove_balance(user_id, bet):
            await interaction.followup.send("Failed to place bet.", ephemeral=True)
            return

        # Determine crash point (weighted towards lower multipliers)
        crash_point = random.uniform(1.01, 10.0)
        if random.random() < 0.3:  # 30% chance of early crash
            crash_point = random.uniform(1.01, 2.0)

        game = {
            'bet': bet,
            'crash_point': crash_point,
            'current_multiplier': 1.00,
            'channel_id': interaction.channel_id,
            'message': None,
            'cashed_out': False
        }

        self.active_games[user_id] = game

        # Create initial embed and view
        embed = self._get_crash_embed(game, interaction.user)
        view = CrashView(self, interaction.user)
        
        msg = await interaction.followup.send(embed=embed, view=view)
        game['message'] = msg

        # Start the crash game loop
        self.bot.loop.create_task(self._run_crash_game(user_id, interaction.user))

    async def _run_crash_game(self, user_id: int, user: discord.User):
        """Run the crash game - increment multiplier until crash or cashout."""
        game = self.active_games.get(user_id)
        if not game:
            return

        try:
            while game['current_multiplier'] < game['crash_point'] and not game['cashed_out']:
                await asyncio.sleep(0.8)  # Update every 0.8 seconds
                
                if user_id not in self.active_games:
                    # Game was ended externally
                    return

                # Increment multiplier
                increment = random.uniform(0.05, 0.15)
                game['current_multiplier'] = min(
                    game['current_multiplier'] + increment,
                    game['crash_point']
                )

                # Update embed
                embed = self._get_crash_embed(game, user)
                try:
                    await game['message'].edit(embed=embed)
                except:
                    # Message was deleted or interaction expired
                    if user_id in self.active_games:
                        del self.active_games[user_id]
                    return

            # Game ended - either crashed or cashed out
            if not game['cashed_out']:
                # Crashed!
                game['current_multiplier'] = game['crash_point']
                embed = self._get_crash_embed(game, user, crashed=True)
                try:
                    await game['message'].edit(embed=embed, view=None)
                except:
                    pass
                
                if user_id in self.active_games:
                    del self.active_games[user_id]

        except Exception as e:
            print(f"Error in crash game: {e}")
            if user_id in self.active_games:
                # Return bet on error
                econ_cog = self.bot.get_cog('Economy')
                if econ_cog:
                    econ_cog._add_balance(user_id, game['bet'])
                del self.active_games[user_id]

    def _get_crash_embed(self, game, user, crashed=False):
        """Create embed for crash game state."""
        multiplier = game['current_multiplier']
        potential_win = int(game['bet'] * multiplier)

        if crashed:
            embed = discord.Embed(
                title="💥 CRASHED! 💥",
                description=f"**Multiplier: {multiplier:.2f}x**\n\nThe game crashed! You lose 🪙 {game['bet']} credits.",
                color=discord.Color.red()
            )
        elif game['cashed_out']:
            embed = discord.Embed(
                title="💰 Cashed Out! 💰",
                description=f"**Multiplier: {multiplier:.2f}x**\n\nYou win 🪙 **{potential_win - game['bet']}** credits!",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="🚀 Crash Game 🚀",
                description=f"**Current Multiplier: {multiplier:.2f}x**\n\nPotential Win: 🪙 **{potential_win}**\n\nCash out before it crashes!",
                color=discord.Color.blue()
            )

        embed.add_field(name="Bet", value=f"🪙 {game['bet']}", inline=True)
        embed.set_footer(text=f"Requested by {user.display_name}", icon_url=user.display_avatar.url)
        
        return embed

    async def cashout(self, interaction: discord.Interaction):
        """Cash out from crash game."""
        user_id = interaction.user.id
        game = self.active_games.get(user_id)

        if not game or game['cashed_out']:
            await interaction.response.send_message("No active crash game found.", ephemeral=True)
            return

        # Mark as cashed out
        game['cashed_out'] = True

        # Calculate winnings
        winnings = int(game['bet'] * game['current_multiplier'])
        
        econ_cog = self.bot.get_cog('Economy')
        if econ_cog:
            econ_cog._add_balance(user_id, winnings)

        # Update embed
        embed = self._get_crash_embed(game, interaction.user)
        embed.set_footer(text=f"Balance: 🪙 {econ_cog.economy[str(user_id)]['balance']}")
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # Clean up
        if user_id in self.active_games:
            del self.active_games[user_id]


class CrashView(discord.ui.View):
    """View with Cash Out button for crash game."""

    def __init__(self, casino_cog, user):
        super().__init__(timeout=60)  # 1 minute timeout
        self.casino_cog = casino_cog
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the game owner to use buttons."""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="💰 Cash Out", style=discord.ButtonStyle.success)
    async def cashout_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.casino_cog.cashout(interaction)

    async def on_timeout(self):
        """Handle timeout - auto cash out."""
        game = self.casino_cog.active_games.get(self.user.id)
        if game and not game['cashed_out']:
            game['cashed_out'] = True
            # Award current multiplier
            econ_cog = self.casino_cog.bot.get_cog('Economy')
            if econ_cog:
                winnings = int(game['bet'] * game['current_multiplier'])
                econ_cog._add_balance(self.user.id, winnings)
            
            if self.user.id in self.casino_cog.active_games:
                del self.casino_cog.active_games[self.user.id]


async def setup(bot):
    await bot.add_cog(Casino(bot))
