import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import logging
from dotenv import load_dotenv
import os
from pytubefix import YouTube
from pytubefix.cli import on_progress
from moviepy import *
import os, shutil




load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command(pass_context = True)
async def join(msg, video):
    if (msg.author.voice):
            print(bot.voice_clients)
            if not(bot.voice_clients):
                channel = msg.author.voice.channel
                print(channel)
                voice = await channel.connect()
            else:
                channel = msg.author.voice.channel
                voice = bot.voice_clients[0]
            voice.play(discord.FFmpegPCMAudio(executable="D:\\ffmpeg\\ffmpeg.exe", source="Audios\\"+video.title+".mp3"))
            print("playback finished")
            await clear()
    else:
        await msg.channel.send("You must be in a vc")   

async def clear():
    folder = 'Videos'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

@bot.command(pass_context = True)
async def leave(ctx):
    if (ctx.voice_client):
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Leaving the vc")
    else:
        await ctx.send("I am not in a vc")

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if "play" in message.content.lower():
        url = message.content.split(" ")
        if len(url) != 2:
            await message.channel.send(f"missing url")
            return
        url = url[1]
        print(url)
        yt = YouTube(url, on_progress_callback = on_progress)
        print(yt.title+".mp3")
        print(os.listdir("Audios"))
        if not ((yt.title+".mp3") in (os.listdir("Audios"))):
            print("going to yt")
            ys = yt.streams.get_highest_resolution()
            ys.download("Videos")
            video = VideoFileClip("Videos\\"+yt.title+".mp4")
            video.audio.write_audiofile("Audios\\"+yt.title+".mp3")

        await message.channel.send(f"{message.author.mention} - Now playing: {yt.title}")
        await join(message,yt)
 
                

bot.run(token, log_handler=handler, log_level=logging.DEBUG)