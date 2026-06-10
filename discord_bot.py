
import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import numpy as np
import re
import math
import random
import aiohttp
import logging
import logging.handlers
import io
# for ascii art
from PIL import Image, ImageFont, ImageDraw
import webbrowser
# import zeeg
import requests
import csv 
import pandas as pd
from scraper import RiotScraper 
from scraper import SheetWriter
#from test_meta import opgg_lp
import random
import asyncio
from scraper import RiotScraper, SheetWriter

riot_api_scraper = RiotScraper()
writer = SheetWriter(sheet_name="Arena Tracker")

# [riot_game_name, tagline, sheet_column_label]  — players[0] is the "primary"
ARENA_PLAYERS = [
    ['Zeegyboogydoog', 'NA1',  'Zeegy'],
    ['Anthotron713',   'NA1',  'Anthotron'],
    ['iLuvNewjeans',   '6884', 'iLuvNewjeans'],
]
discord.utils.setup_logging(level=logging.INFO, root=False)
person = 'haerin'
lp = 1
CommandKey = '!'
load_dotenv()
intents = discord.Intents.all()
intents.message_content = True
client = discord.Client(intents=discord.Intents.default())
# bot = commands.Bot(command_prefix='.', intents=intents,description="Making Alex question life decisions")
# tree = discord.app_commands.CommandTree(bot)
token = os.getenv("DISCORD_TOKEN")
#print(f"Token retrieved: {token}")
owner = os.getenv("OWNER_ID")
GIF_FOLDER = os.getenv("GIF_FOLDER")
TENOR_API_KEY = os.getenv("TENOR_API_KEY")

async def load_extensions():
    cogs_dir = "./cogs"
    if not os.path.exists(cogs_dir):  # Check if cogs folder exists
        print("Cogs directory not found. Skipping extension loading.")
        return

    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py"):
            if filename.startswith("llm"):  # Skip specific files
                continue
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded cog: {filename[:-3]}")
            except Exception as e:
                print(f"Failed importing cog {filename[:-3]}: {e}")
active_cogs = set()


class Bot(commands.Bot):
    def __init__(self, intents: discord.Intents, **kwargs):
        super().__init__(
            command_prefix=commands.when_mentioned_or("."),
            intents=intents,
            description="Making Alex question life decisions",
            **kwargs,
        )


bot = Bot(intents=intents, help_command=None)


@bot.event
async def on_ready():
    activity = discord.Game("", type=3)
    await bot.change_presence(status=discord.Status.online, activity=activity)
    await load_extensions()

    print(active_cogs)
    print("Logged in as a bot {0.user}".format(bot))


@bot.tree.command(name="hello")
@app_commands.describe(member="The member you want me to say hi to.")
async def hello(interaction, member: discord.Member):
    await interaction.response.send_message(f"Hello {member}")


@bot.tree.command(name="sync", description="Owner only")  # manually sync
async def sync(interaction: discord.Interaction):
    print(type(owner), type(interaction.user.id))
    if interaction.user.id == int(owner):
        synced = await bot.tree.sync()
        response = f"Command tree synced. {synced}, Number synced: {len(synced)}"
        print(response)
        # await interaction.response.send_message(response)
    else:
        await interaction.response.send_message(
            "You must be the owner to use this command!"
        )


@bot.command()
async def test(ctx, arg):
    embed = discord.Embed(description=(f"{arg} Test"), colour=discord.Colour.purple())
    await ctx.send(embed=embed)


@bot.command()
async def ping(ctx):
    await ctx.send("Pong")



def get_gif(searchTerm):
    if searchTerm == 'gaeul':
        temp_num = 24178363
        
    stochastic_term = random.randint(1, 20)
    append = f'%22{searchTerm}%22 kpop girl {stochastic_term}' 

    url = f"https://tenor.googleapis.com/v2/search?q={append}&key={TENOR_API_KEY}&limit=10"
    response = requests.get(url)
    
    if response.status_code != 200:
        return "We have problemo"
    
    data = response.json()
    if "results" in data and len(data["results"]) > 0:
        return random.choice(data["results"])["media_formats"]["gif"]["url"]
    
    return "No GIF found!"

#Riot API Scraper Section



@bot.event
async def on_message(message):
    print(message.content, message.author.id, message.author)
    if message.author == bot.user:
        return

    if message.content.startswith("$Update"):
        results, match_id = await asyncio.to_thread(riot_api_scraper.scrape_shared_game, ARENA_PLAYERS)

        if match_id is None:
            await message.channel.send("No recent Arena game found.")
        elif results is None:
            await message.channel.send("Latest Arena game already recorded — nothing new.")
        else:
            game_num = await asyncio.to_thread(writer.next_game_number)
            await asyncio.to_thread(writer.add_game, game_num, results)
            riot_api_scraper.mark_recorded(match_id)   
            found = ", ".join(results)

            
            print(results['Zeegy'][0])

            
            await message.channel.send(f"Recorded Arena game #{game_num} ({found}) ✅")
    if message.content.startswith("!"):
        searchTerm = message.content[1:]  # Remove the "!" to get the search term... ow for a ot that deteries if it is a guy or girl. 
        gif_url = get_gif(searchTerm)
        
        if gif_url.startswith("http"): 
            await message.channel.send(gif_url)
        else:
            await message.channel.send(f"❌ {gif_url}")
    
    await bot.process_commands(message) 

    
    if message.content.startswith("aespi"):
        parts = message.content.split()
        if parts[1].lower() == 'ningning':
            location = 3
        elif parts[1].lower() == 'giselle':
            location = 1
        elif parts[1].lower() == 'karina':
            location = 2
        else:
            location = 4
        
        temp_list = []
        if message.attachments:
            for attatchment in message.attachments:
                #if attatchment.filename.lower().endswith(".png"):
                tempper_adder = []
                print("DETECTION", attatchment.url)
                for j in range(4):
                    if j + 1 != location:
                        tempper_adder.append(0)
                    else:
                        tempper_adder.append(attatchment.url)
                temp_list.append(tempper_adder)

            
        with open('DL_kpop_idol_detection/aespa_added_png.csv', 'a') as file:
            writer_object = csv.writer(file)

            for i in range(len(temp_list)):
                writer_object.writerow(temp_list[i])

        message.channel.send("done")

    if message.author.id == 406797636402806785:
        await message.add_reaction("🐐")
    
    if message.author.id == 456589647670280205:
        await message.add_reaction("I")
        await message.add_reaction("❓")
        await message.add_reaction("❔")

    if message.author.id == 433764142999011350:
        if random.randint(1, 100) == 1:
            await message.add_reaction("O")
            await message.add_reaction("B")
            await message.add_reaction("E")
            await message.add_reaction("R")
            await message.add_reaction("T")
            
    

    # if message.content.upper() == '!KARINA':
    #     num = random.randint(1, 4)
    #     file_path = os.path.join("gifs", f'karina_{num}.gif')
    #     file = discord.File(file_path, filename="karina_smile.gif")
    #     await message.channel.send(file = file)

    if message.author.id == 496827202646835202:
        a = random.randint(1, 100)
        if a == 1:
            await message.channel.send("I HATE WOMEN")

    if message.content.upper() == "NEWJEANS":
        try:
        # Get all GIF files in the folder
            gif_files = [f for f in os.listdir(GIF_FOLDER) if f.endswith(".gif")]

            if not gif_files:
                await message.channel.send("❌ No GIFs found in `public_save_newjeans`.")
                return

        # Pick a random GIF
            random_gif = random.choice(gif_files)
            file_path = os.path.join(GIF_FOLDER, random_gif)

        # Send the GIF
            file = discord.File(file_path, filename=random_gif)
            await message.channel.send(file=file)

        except Exception as e:
            print(f"❌ Error selecting GIF: {e}")
            await message.channel.send("⚠️ Something went wrong while selecting a GIF.")
       
   

    
    if message.content == "TALENT":
        await message.channel.send('https://lolchess.gg/profile/na/Zeegyboogydoog-NA1/set12')

    if message.content == "ollie jen":
        await message.channel.send('https://tactics.tools/player/na/Meowmer05')
        #await message.channel.send(f'Ollie jen is hardstuck {} lp')

    if message.content.startswith("!gif_add"):
        print("hi")
        parts = message.content.split()

        msg = parts[1]
        gif_url = msg  # Replace with actual GIF URL
        print(msg)
        env_path = os.path.join('gifs', '.env')
       # load_dotenv(dotenv_path = env_path)

        with open('gifs/links.txt', 'a') as file:
            file.write(msg + '\n') #adds to giant txt file. 

        await message.channel.send('added')
        return 

    
    if message.content.startswith("!gif_spawn"):
        with open('gifs/links.txt', 'r') as file:
            lines = [line.strip() for line in file.readlines()] 

            if not lines:
                await message.channel.send("broke xd")
                return 
            var = random.randint(0, len(lines) -1 )
            random_gif = lines[var]
            

            
            await message.channel.send(lines[var])
            return 
        
    if message.content.startswith("!gif_delete"):
        parts = message.content.split()
        url = parts[1]
        with open('gifs/links.txt', 'a') as file:
            for j in file:
                if j == url:
                    await message.channel.send("i havent' finished htis yet xd")
                    return 

    
    if message.content == "OBERT":
        await message.channel.send('https://www.op.gg/summoners/na/Fobert-7896')

    if "ANDY" in message.content:
        await message.channel.send('https://tactics.tools/player/na/0pp0rtunities')
   
    if "OLLIE JEN" in message.content:
        await message.channel.send('https://tactics.tools/player/na/soberti')
        SUMMONER_NAME = "Soberti"
        TAGLINE = "#INSEC"
   
    if "JESS" in message.content:
        await message.channel.send('https://tactics.tools/player/na/pookie%20ezreal')
    if "NEIGH" in message.content:
        await message.channel.send('https://tactics.tools/player/na/neighborhoodnunu')

    if "ETHAN" in message.content:
        await message.channel.send('Happy borgsday Ethan 1/30')
        

    await bot.process_commands(message)


    
bot.run(token)