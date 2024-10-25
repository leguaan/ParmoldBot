
async def tryHandleBadBot(message):
    bad_words = [
        "bad bot", "halb bot", "loll bot", "rumal bot", "idioot", "tüütu", "munn", "perse",
        "debiilik", "lollakas", "põmmpea", "tolvan", "värdjas", "mölakas", "idikas", "idioot bot"
    ]
    if any(word in message.content.lower() for word in bad_words):
        await message.add_reaction('😢')

async def tryHandleGoodBot(client, message):
    good_words = [
        "good bot", "hea bot", "tubli bot", "aitäh", "tubli", "suurepärane", "vinge",
        "äge", "mulle meeldib", "fantastiline", "tänan", "tänud", "huvä"
    ]
    if any(word in message.content.lower() for word in good_words):
        emoji = client.get_emoji(1291820499420053677)
        await message.add_reaction(emoji)
