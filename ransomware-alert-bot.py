import discord
import asyncio
import requests
import json
from discord.ext import commands, tasks
from datetime import datetime

# Configuration
TOKEN = "" # You will need to create an API token on Discord
CHANNEL_ID =  # Replace with your Discord channel ID
RANSOMWARE_API_URL = "https://api.ransomware.live/v2/recentvictims"  # Example API (adjust as needed)
CHECK_INTERVAL = 600  # Check every 10 minutes
ROLE_ID = # Replace with the Role's Discord ID
REPORTED_ATTACKS_FILE = "reported_attacks.json"  # File to store reported attacks

# Bot setup
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load reported attacks from file
try:
    with open(REPORTED_ATTACKS_FILE, "r") as file:
        reported_attacks = set(json.load(file))
    print(f"Loaded reported attacks: {reported_attacks}")
except (FileNotFoundError, json.JSONDecodeError):
    reported_attacks = set()
    print("No reported attacks file found or file is empty. Starting with an empty set.")

async def fetch_ransomware_updates():
    try:
        response = requests.get(RANSOMWARE_API_URL)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        print("API Response:", data)  # Log the API response
        return data
    except Exception as e:
        print(f"Error fetching ransomware updates: {e}")
        return None

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_ransomware_updates():
    global reported_attacks
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel not found!")
        return

    updates = await fetch_ransomware_updates()
    if updates:
        new_attacks = []

        for attack in updates:
            # Create a unique identifier for the attack
            unique_id = f"{attack.get('victim', 'Unknown')}_{attack.get('group', 'Unknown')}"
            print(f"Generated unique_id: {unique_id}")
            if unique_id not in reported_attacks:
                new_attacks.append(attack)
                reported_attacks.add(unique_id)
            else:
                print(f"Attack with unique_id {unique_id} already reported.")

        for attack in new_attacks:
            print(f"Processing attack: {attack}")  # Log the attack to inspect its structure

            # Adjust the key based on the actual structure of the API response
            discovered = attack.get('discovered', 'Unknown')  # Assuming the API provides a date
            if discovered != 'Unknown':
                try:
                    discovered_dt = datetime.fromisoformat(discovered)
                    discovered = discovered_dt.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    print(f"Invalid date format: {discovered}")

            victim = attack.get('victim', 'Unknown')
            group = attack.get('group', 'Unknown')
            url = attack.get('url', 'N/A')
            image_url = attack.get('image_url', '')  # Assuming the API provides an image URL

            embed = discord.Embed(
                title="🚨 **New Ransomware Attack Detected!** 🚨",
                description=f"📅 Discovered: {discovered}\n"
                            f"💻 Victim: {victim}\n"
                            f"🎭 Group: {group}\n"
                            f"🔗 [More info]({url})",
                color=discord.Color.red()
            )
            if image_url:
                embed.set_image(url=image_url)

            role_mention = f"<@&{ROLE_ID}>"
            print(f"Sending message to channel: {channel.id}")
            await channel.send(content=role_mention, embed=embed)

        # Save reported attacks to file
        with open(REPORTED_ATTACKS_FILE, "w") as file:
            json.dump(list(reported_attacks), file)
        print(f"Saved reported attacks: {reported_attacks}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_ransomware_updates.start()

bot.run("") # Put your API token in here
