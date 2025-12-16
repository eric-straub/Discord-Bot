"""Casino cog — gambling games like blackjack where users can bet credits."""

import discord
from discord.ext import commands
from discord import app_commands
import random


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


async def setup(bot):
    await bot.add_cog(Casino(bot))
