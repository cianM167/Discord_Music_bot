import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import logging
from dotenv import load_dotenv
import os
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

def finished(error):
    print("after running")
    print(error)
    if len(queue) == 0:
        playing[0] = 0
    else:
        voice = bot.voice_clients[0]
        video = queue.pop(0)
        voice.play(discord.FFmpegPCMAudio(executable="D:\\ffmpeg\\ffmpeg.exe", source="Audios\\"+video+".mp3"),after=finished)


@bot.command(pass_context = True)
async def join(ctx, video):
    if (ctx.voice_client):
        await play(ctx,video)
    if (ctx.author.voice):
        channel = ctx.message.author.voice.channel
        await channel.connect()
        await play(ctx,video)
    else:
        await ctx.channel.send("You must be in a vc")   

@bot.command(pass_context = True)
async def play(ctx,video):   
    if not(ctx.voice_client.is_playing()):
        print("adding song")
        await ctx.channel.send(f"{ctx.author.mention} - Now playing: {video.title}")
        ctx.voice_client.play(discord.FFmpegPCMAudio(executable="D:\\ffmpeg\\ffmpeg.exe", source="Audios\\"+video.title+".mp3"),after=finished)
    else:
        print("queueing song")
        await ctx.channel.send(f"{ctx.author.mention} - Queueing: {video.title}")
        server_queue[ctx.guild.id].append(video.title)
        print(server_queue[ctx.guild.id])
        queue.append(video.title)
        print(queue)
    #print("playback finished")
    await clear()

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
            ys.download("m4as")
            filename = yt.title + ".m4a"
            audio = AudioSegment.from_file(os.path.join("m4as", filename))
            audio.export("Audios\\"+yt.title+".mp3", format="mp3")

        ctx = await bot.get_context(message)
        server_queue[ctx.guild.id] = []
        await join(ctx,yt)
 
    if "!queue" in message.content.lower():
        await message.channel.send(f"{queue}")            

bot.run(token, log_handler=handler, log_level=logging.DEBUG)