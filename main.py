import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if 'mhm' in message.content:
        await message.channel.send('Ta on jõuksis')

@bot.command
async def remindme(ctx, *, arg):
    await ctx.send('Tee PR! Ma ei tea kuidas seda progeda.')


bot.run(os.environ.get('TOKEN'))