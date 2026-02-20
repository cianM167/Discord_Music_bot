#!/usr/bin/env python3

import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import logging
from dotenv import load_dotenv
from pytubefix import YouTube
from pytubefix.cli import on_progress
from pytubefix import Search
from pydub import AudioSegment
import os, shutil

#maybe just download mp4a if it is support


load_dotenv() 
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


bot = commands.Bot(command_prefix='!', intents=intents)
playing = []
playing.append(0)
queue = []
server_queue = {}

ffmpeg_options = {
    'options': '-vn -ac 2 -ar 48000',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

def finished(error, ctx):
    print(f"After running in guild: {ctx.guild.name}")
    if error:
        print(f"Player error: {error}")

    # Use the local server_queue instead of a global list if possible
    guild_id = ctx.guild.id
    
    if guild_id not in server_queue or len(server_queue[guild_id]) == 0:
        print("Queue is empty.")
    else:
        voice = ctx.voice_client
        next_video_title = server_queue[guild_id].pop(0)
        
        # Define source (using the M4A/FFmpeg improvements from before)
        source = discord.FFmpegPCMAudio(
            executable="ffmpeg", 
            source=f"Audios/{next_video_title}.m4a"
        )
        
        # Pass ctx again in the next callback recursion
        voice.play(source, after=lambda e: finished(e, ctx))


@bot.command(pass_context = True)
async def join(ctx, video):
    if (ctx.voice_client):
        await play(ctx,video)
    if (ctx.author.voice):
        channel = ctx.message.author.voice.channel
        vc = await channel.connect()
        await play(ctx,video)
    else:
        await ctx.channel.send("You must be in a vc")   

@bot.command(pass_context = True)
async def play(ctx, video):   
    if not ctx.voice_client.is_playing():
        source = discord.FFmpegPCMAudio(executable="ffmpeg", source=f"Audios/{video.title}.m4a")
        
        # Use a lambda to pass both the error (e) and the context (ctx)
        ctx.voice_client.play(source, after=lambda e: finished(e, ctx))
        
        await ctx.channel.send(f"Now playing: {video.title}")
    else:
        # Add to queue logic...
        server_queue[ctx.guild.id].append(video.title)
        await ctx.channel.send(f"Added to queue: {video.title}")

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
    
    if "!play" in message.content.lower():
        if "youtube.com" in message.content:
            url = message.content.split(" ")
            if len(url) != 2:
                await message.channel.send(f"missing url")
                return
            url = url[1]
        else:
            title = message.content.split(" ", 1)
            print(title)
            result = Search(title[1])
            url = (result.videos[0]).watch_url
        
        print(url)
        yt = YouTube(url, on_progress_callback = on_progress)
        print(yt.title+".mp3")
        print(os.listdir("Audios"))
        if not ((yt.title+".mp3") in (os.listdir("Audios"))):
            print("going to yt")
            ys = yt.streams.get_audio_only()
            ys.download(output_path = "Audios", filename = f"{yt.title}.m4a")
            

        ctx = await bot.get_context(message)
        server_queue[ctx.guild.id] = []#need to check that it doesnt exist already
        await join(ctx,yt)
 
    if "!queue" in message.content.lower():
        await message.channel.send(f"{server_queue[ctx.guild.id]}")            

bot.run(token, log_handler=handler, log_level=logging.DEBUG)