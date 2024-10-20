import discord
import os
import asyncio
import sqlite3
import re
from datetime import datetime, timedelta
import pytz

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Create or connect to the database
conn = sqlite3.connect('reminders.db')
c = conn.cursor()

# Create a table to store reminders if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS reminders (
    user_id INTEGER,
    channel_id INTEGER,
    reminder_message TEXT,
    remind_at DATETIME
)''')
conn.commit()

# Function to convert time with units into seconds
def convert_time_to_seconds(time_str):
    time_regex = r"(\d+)\s*(second|minute|hour|day|month|year)s?"
    match = re.match(time_regex, time_str.lower())

    if not match:
        return None

    value, unit = int(match.group(1)), match.group(2)

    time_multipliers = {
        'second': 1,
        'minute': 60,
        'hour': 3600,
        'day': 86400,
        'month': 2592000,  # Assuming 30 days in a month
        'year': 31536000   # 365 days
    }

    return value * time_multipliers.get(unit, 0)

# Function to save a reminder to the database
def save_reminder(user_id, channel_id, message, remind_at):
    c.execute("INSERT INTO reminders (user_id, channel_id, reminder_message, remind_at) VALUES (?, ?, ?, ?)",
              (user_id, channel_id, message, remind_at))
    conn.commit()

# Function to load reminders and resume waiting for them
async def load_reminders():
    c.execute("SELECT rowid, * FROM reminders")
    reminders = c.fetchall()

    for reminder in reminders:
        rowid, user_id, channel_id, message, remind_at = reminder
        remind_at_dt = datetime.strptime(remind_at, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()

        # Calculate remaining time
        remaining_seconds = (remind_at_dt - now).total_seconds()

        if remaining_seconds > 0:
            # If time is still in the future, set a task to wait for it
            asyncio.create_task(schedule_reminder(rowid, user_id, channel_id, message, remaining_seconds))
        else:
            # If the reminder time has already passed, send the reminder immediately
            await send_reminder(rowid, user_id, channel_id, message)

# Function to wait and send the reminder
async def schedule_reminder(rowid, user_id, channel_id, message, wait_time):
    await asyncio.sleep(wait_time)
    await send_reminder(rowid, user_id, channel_id, message)

# Function to send the reminder
async def send_reminder(rowid, user_id, channel_id, message):
    channel = client.get_channel(channel_id)
    if channel:
        await channel.send(f"<@{user_id}>, reminder: {message}")

    # Delete reminder from database after sending
    c.execute("DELETE FROM reminders WHERE rowid = ?", (rowid,))
    conn.commit()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await load_reminders()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if 'mhm' in message.content.lower():
        await message.channel.send('Ta on jõuksis!')

    # Handle the $remindme command
    if message.content.startswith('$remindme'):
        try:
            # Example format: $remindme "Your reminder message" 3 days
            command_pattern = r'\$remindme\s*"(.+)"\s*(\d+\s*\w+)'
            match = re.match(command_pattern, message.content)

            if not match:
                await message.channel.send("Please use the correct format: $remindme \"your message\" time (e.g., 3 days).")
                return

            reminder_message = match.group(1)
            time_str = match.group(2)

            # Convert time string to seconds
            time_in_seconds = convert_time_to_seconds(time_str)
            if time_in_seconds is None:
                await message.channel.send("Invalid time format! Use a number followed by a unit (seconds, minutes, hours, days, months, or years).")
                return

            # Calculate when the reminder should be triggered
            remind_at = datetime.now() + timedelta(seconds=time_in_seconds)

            # Save the reminder to the database
            save_reminder(message.author.id, message.channel.id, reminder_message, remind_at.strftime('%Y-%m-%d %H:%M:%S'))

            # Set a task to wait and send the reminder
            asyncio.create_task(schedule_reminder(None, message.author.id, message.channel.id, reminder_message, time_in_seconds))

            await message.channel.send(f"Reminder set! I'll remind you to \"{reminder_message}\" in {time_str}.")

        except Exception as e:
            await message.channel.send(f"Something went wrong: {str(e)}")

    if message.content.startswith('$silvertime'):
        sydney_timezone = pytz.timezone('Australia/Sydney')
        sydney_time = datetime.now(sydney_timezone)
        await message.channel.send(f"Time in Sydney, Australia is {sydney_time.strftime('%H:%M')}")

        
    if message.content.startswith('$ristotime'):
        ams_tz = pytz.timezone('Europe/Amsterdam')
        ams_time = datetime.now(ams_tz)
        await message.channel.send(f"Time in Maaskantje, Netherlands is {ams_time.strftime('%H:%M')}")

    if "bad bot" in message.content.lower():
        await message.add_reaction('😢')

    if message.content.startswith('$help'):
        await message.channel.send('KYS')

client.run(os.environ.get('TOKEN'))
