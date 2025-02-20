import discord
from discord import app_commands
from discord.ext import commands
import typing
import sqlite3
import logging

class BankCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = 'data/gambling.db'
        self.conn = None
        self._create_tables()


        self.ctx_menu = app_commands.ContextMenu(
            name='Balance',
            callback=self._get_balance_ctxmenu
        )
        self.bot.tree.add_command(self.ctx_menu)

    def _create_tables(self):
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    balance INTEGER DEFAULT 0,
                    last_daily TEXT
                )
            ''')
            conn.commit()

    def _get_connection(self):
        if not self.conn:
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        return self.conn

    async def _get_balance_ctxmenu(self, interaction: discord.Interaction, member: discord.Member):
        balance = self.get_balance(member.id)
        await interaction.response.send_message(content=f'{member} omab {balance} eurot.')

    @app_commands.command(name="balance")
    async def _get_balance_cmd(self, interaction: discord.Interaction, member: typing.Optional[discord.Member]=None):
        user = interaction.user if member is None else member
        balance = self.get_balance(user.id)
        await interaction.response.send_message(content=f'{user} omab {balance} eurot.')

    def withdraw(self, user: discord.User | discord.Member, amount: int)->bool:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET balance = balance - ? 
                WHERE user_id = ? AND balance >= ?
            ''', (amount, user.id, amount))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Failed to withdraw: {e}")
            return False

    def withdraw_limitless(self, user: discord.User | discord.Member, amount: int):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET balance = balance - ? 
                WHERE user_id = ?
            ''', (amount, user.id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Failed to withdraw: {e}")
            return False

    def deposit(self, user: discord.User | discord.Member, amount: int):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET balance = balance + ? 
                WHERE user_id = ?
            ''', (amount, user.id))
            conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to deposit {user.id}: {e}")

    def get_balance(self, user: discord.User | discord.Member)->int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user.id,))
            result = cursor.fetchone()

            if not result:
                cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user.id,))
                conn.commit()
                return 0

            return result
        except sqlite3.Error as e:
            logging.error(f"Error getting user {user.id}: {e}")
            return 0
    

async def setup(bot: commands.Bot):
    await bot.add_cog(BankCog(bot))