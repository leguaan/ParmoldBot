from ollama import AsyncClient
import logging
import re

def clean_response(response):
    return re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()

async def try_handle_ai(client, message):
    mention = f"<@{client.user.id}>"
    mention_alt = f"<@!{client.user.id}>"
    if mention in message.content or mention_alt in message.content:
        async with message.channel.typing():
            content = message.content.replace(f"<@{client.user.id}>", "").strip()
            ai_input = {'role': 'user', 'content': f"{content}. Keep answer under 1000 char!"}
            response = await AsyncClient(host='http://ollama:11434').chat(model='deepseek-r1:1.5b', messages=[ai_input])
            logging.info(response)
            await message.reply(clean_response(response.message.content))