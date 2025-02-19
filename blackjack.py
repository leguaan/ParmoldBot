import discord
from discord.ext import commands
import random

def create_deck():
    suits = ['♠', '♥', '♦', '♣']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = [f"{rank}{suit}" for suit in suits for rank in ranks]
    random.shuffle(deck)
    return deck

def card_value(card):
    rank = card[:-1]  # drop the suit
    if rank in ['J', 'Q', 'K']:
        return 10
    if rank == 'A':
        return 11  # will adjust later for aces
    return int(rank)

def hand_value(hand):
    total = sum(card_value(card) for card in hand)
    aces = sum(1 for card in hand if card[:-1] == 'A')
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

class BlackjackView(discord.ui.View):
    def __init__(self, author_id, deck, player_hand, dealer_hand):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.deck = deck
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.game_over = False

    async def update_message(self, interaction: discord.Interaction):
        content = (
            f"**Player's hand:** {' '.join(self.player_hand)} (Score: {hand_value(self.player_hand)})\n"
            f"**Dealer's hand:** {' '.join(self.dealer_hand)}"
        )
        if self.game_over:
            p_score = hand_value(self.player_hand)
            d_score = hand_value(self.dealer_hand)
            if p_score > 21:
                content += "\nYou busted! Dealer wins."
            elif d_score > 21:
                content += "\nDealer busted! You win!"
            elif d_score < p_score:
                content += "\nYou win!"
            elif d_score > p_score:
                content += "\nDealer wins!"
            else:
                content += "\nPush!"
            for child in self.children:
                child.disabled = True
        await interaction.response.edit_message(content=content, view=self)

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        # Deal another card
        if self.deck:
            self.player_hand.append(self.deck.pop())
        # If busted, end game
        if hand_value(self.player_hand) > 21:
            self.game_over = True
        await self.update_message(interaction)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red)
    async def stand(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        # Dealer draws until reaching 17 or more
        while hand_value(self.dealer_hand) < 17 and self.deck:
            self.dealer_hand.append(self.deck.pop())
        self.game_over = True
        await self.update_message(interaction)

class BlackjackCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def blackjack(self, ctx: commands.Context, bet:int):
        deck = create_deck()
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop()]
        content = (
            f"**Player's hand:** {' '.join(player_hand)} (Score: {hand_value(player_hand)})\n"
            f"**Dealer's hand:** {' '.join(dealer_hand)}"
        )
        view = BlackjackView(ctx.interaction.user.id, deck, player_hand, dealer_hand)
        await ctx.send(content=content, view=view)