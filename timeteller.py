from datetime import datetime
import pytz

async def tryHandleSilverTime(message):
    if message.content.startswith('$silvertime'):
        sydney_timezone = pytz.timezone('Australia/Sydney')
        sydney_time = datetime.now(sydney_timezone)
        await message.channel.send(f"Time in Sydney, Australia is {sydney_time.strftime('%H:%M')}")

async def tryHandleRistoTime(message):
    if message.content.startswith('$ristotime'):
        ams_tz = pytz.timezone('Europe/Amsterdam')
        ams_time = datetime.now(ams_tz)
        await message.channel.send(f"Time in Maaskantje, Netherlands is {ams_time.strftime('%H:%M')}")
