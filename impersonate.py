import re
import logging
import discord
import io

async def try_handle_impersonation(client, message):
    if message.content.startswith('$react'):
        await message.delete()
        command_pattern = r'\$react (\d*) (\d*)'
        match = re.match(command_pattern, message.content)
        logging.debug('$react {msg_id} {emoji_id} called by {author_name}({author_id})', author_name=message.author.global_name,author_id=message.author.id, msg_id=match.group(1), emoji_id=match.group(2))
        if not match:
            return
        
        sub = await message.channel.fetch_message(int(match.group(1)))
        emoji = client.get_emoji(int(match.group(2)))
        await sub.add_reaction(emoji)
    if message.content.startswith('$impersonate'):
        attachments = []
        logging.debug('$impersonate called by {author_name}({author_id})', author_name=message.author.global_name,author_id=message.author.id)
        if message.attachments:
            attachments = [await attachment.read() for attachment in message.attachments]
        command_pattern = r'\$impersonate (.*)'
        content = None
        match = re.match(command_pattern, message.content)
        if match:
            content = match.group(1)
        await message.delete()
        await message.channel.send(
            content=content,
            files=[discord.File(fp=io.BytesIO(attachment), filename='output.png') for attachment in attachments]
            )
        
