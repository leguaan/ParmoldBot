import random


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


async def tryHandleReactionBot(client, message):
    parmold_emoji = [
        1291858408072417321, 1291859256013885540, 1291821346690568365, 1292772836557193216, 1291823258336759878,
        1291823259444052000, 1291820495477411891, 1292918601661157479, 1292918596628119592, 1291816855048290417,
        1291816189479227454, 1292918603901042800, 1291858993429483540, 1292918605117132852, 1291823260593553571,
        1292452385305788478, 1292918595374022801, 1291821627855605761, 1292919775797973125, 1291858408072417321,
        1291858430562144268, 1292918606392459358, 1291820488573718528, 1291820486296338432, 1291820484891115716,
        1291820489895055492, 1291820502129840264, 1291820483062399069, 1297204982650507274, 1291820492658839694,
        1297204248752427019, 1297204247502520360, 1297204980847087686, 1297204246105690154, 1294954438322032731,
        1291820491287560313, 1292748187194363998, 1293643998291824760, 1291820494001143850, 1291820499420053677,
        1291822640050475111, 1292918608347004981, 1292918600033767444, 1296889495609806969, 1292918598326554677
    ]
    if random.randint(1, 1000) <= 10:  # 1 in 100
        random_emoji_id = random.choice(parmold_emoji)
        emoji = client.get_emoji(random_emoji_id)
        if emoji:
            await message.add_reaction(emoji)
