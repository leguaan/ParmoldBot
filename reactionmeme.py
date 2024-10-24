import discord
import random
import requests
from transformers import pipeline
from bs4 import BeautifulSoup

# Create a pre-trained sentiment-analysis pipeline
classifier = pipeline("sentiment-analysis")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Define emotions and search terms for images
search_terms = {
    "happy": ["dank meme happy reaction image", "funny happy meme png", "happy reaction image"],
    "angry": ["angry meme reaction image", "angry meme png", "angry reaction face"],
    "neutral": ["neutral face meme png", "meh reaction image", "neutral meme png"],
    "bored": ["bored meme reaction image", "bored face png", "boring meme png"]
}

# Randomly classify 1 in 100 messages
def should_classify_message():
    return True or (random.randint(1, 100) == 1)  # 1 in 100 chance

# Map sentiment labels to custom emotions
def map_sentiment_to_emotion(sentiment):
    if sentiment == "POSITIVE":
        return random.choice(["happy", "neutral"])  # Map positive to happy or neutral
    elif sentiment == "NEGATIVE":
        return "angry"  # Map negative to angry
    else:
        return "bored"  # Default to bored

# Function to scrape images from DuckDuckGo Image Search
def fetch_image_url(emotion):
    query = random.choice(search_terms[emotion])
    url = f"https://duckduckgo.com/?q={query}&t=h_&iar=images&iax=images&ia=images"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract image URLs from the HTML content
    images = soup.find_all('img', {'class': 'tile--img__img'})
    
    # Pick a random image URL
    if images:
        image_url = random.choice(images)['src']
        return image_url
    else:
        return None


async def tryHandleReactionMeme(message):
    if should_classify_message():
        # Classify the message using the pre-trained model
        result = classifier(message.content)[0]
        sentiment_label = result['label']
        
        # Map the sentiment label to a custom emotion
        emotion = map_sentiment_to_emotion(sentiment_label)
        
        # Fetch a relevant image URL based on the emotion
        image_url = fetch_image_url(emotion)
        
        if image_url:
            # Send the classified emotion and the image
            await message.channel.send(f'🤖 I think this message is: **{emotion}**', embed=discord.Embed().set_image(url=image_url))
        else:
            # If no image is found, send only the emotion
            await message.channel.send(f'🤖 I think this message is: **{emotion}**, but I couldn\'t find an image.')
