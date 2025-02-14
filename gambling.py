import sqlite3
from datetime import datetime, timedelta
import logging
import random
from discord import Message

logging.basicConfig(level=logging.INFO)
conn = sqlite3.connect('data/gambling.db')
c = conn.cursor()

c.execute(
    '''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0,
        last_daily TEXT
    )
    '''
)
conn.commit()


def get_user(user_id: int):
    try:
        c.execute("SELECT user_id, balance, last_daily FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row is None:
            c.execute("INSERT INTO users (user_id, balance, last_daily) VALUES (?, ?, ?)", (user_id, 0, None))
            conn.commit()
            return user_id, 0, None
        return row
    except sqlite3.Error as e:
        logging.error(f"Error retrieving user {user_id}: {e}")
        return user_id, 0, None


def update_user_balance(user_id: int, new_balance: int):
    try:
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error updating balance for user {user_id}: {e}")


def update_last_daily(user_id: int, timestamp: str):
    try:
        c.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (timestamp, user_id))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error updating last daily for user {user_id}: {e}")


async def try_handle_daily(message: Message):
    if not message.content.startswith('$daily'):
        return
    user_id = message.author.id
    user = get_user(user_id)
    now = datetime.now()

    if user[2]:
        try:
            last_daily = datetime.fromisoformat(user[2])
        except ValueError:
            last_daily = None

        if last_daily and (now - last_daily) < timedelta(days=1):
            remaining = timedelta(days=1) - (now - last_daily)
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            await message.channel.send(f"Juba said oma raha. Proovi uuesti {hours}h {minutes}m pärast!")
            return

    bonus = 1000
    new_balance = user[1] + bonus
    update_user_balance(user_id, new_balance)
    update_last_daily(user_id, now.isoformat())
    await message.channel.send(f"Said oma 100 eurot! Su uus balanss on {new_balance} eurot.")


async def try_handle_balance(message: Message):
    if not message.content.startswith('$balance'):
        return

    user_id = message.author.id
    user = get_user(user_id)
    await message.channel.send(f"Sul on hetkel {user[1]} eurot. Aeg võita, tšempion!")


async def try_handle_bet(message: Message):
    if not message.content.startswith('$bet'):
        return
    parts = message.content.split()

    if len(parts) < 3:
        await message.channel.send("Vale formaat! Kasuta: $bet <amount> <red/black>")
        return

    try:
        amount = int(parts[1])
        if amount <= 0 or amount > 1000000:
            raise ValueError
    except ValueError:
        await message.channel.send("Panuse summa peab olema positiivne arv (max 1,000,000).")
        return

    bet_choice = parts[2].lower()
    if bet_choice not in ['red', 'black']:
        await message.channel.send("Vale panuse valik! Vali 'red' või 'black'.")
        return

    user_id = message.author.id
    user = get_user(user_id)
    if amount > user[1]:
        await message.channel.send("Sul pole piisavalt raha selle panuse jaoks!")
        return

    # Simulate a roulette spin (0-36)
    number = random.randint(0, 36)
    red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    result_color = 'red' if number in red_numbers else 'black' if number != 0 else 'green'

    if result_color == bet_choice:
        winnings = amount  # 1:1 payout
        new_balance = user[1] + winnings
        result_message = f"Pall maandus {number} ({result_color}). Võitsid {winnings} eurot! Su uus balanss on {new_balance} eurot."
    else:
        new_balance = user[1] - amount
        result_message = f"Pall maandus {number} ({result_color}). Kaotasid {amount} eurot. Su uus balanss on {new_balance} eurot."

    update_user_balance(user_id, new_balance)
    await message.channel.send(result_message)
