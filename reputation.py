
async def tryHandleBadBot(message):
    if "bad bot" in message.content.lower():
        await message.add_reaction('😢')

async def tryHandleGoodBot(client, message):
    if "good bot" in message.content.lower():
        emoji = client.get_emoji(1291820499420053677)
        await message.add_reaction(emoji)
