import discord
from discord import app_commands
from discord.ext import commands
from gambling import Database, DB_NAME
db = Database(DB_NAME)

class BankCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name='Balance',
            callback=self.get_balance
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def get_balance(self, interaction: discord.Interaction, member: discord.Member):
        balance, _ = db.get_user_balance(member.id)
        await interaction.response.send_message(content=f'{member} omab {balance} eurot.')


async def setup(bot: commands.Bot):
    await bot.add_cog(BankCog(bot))