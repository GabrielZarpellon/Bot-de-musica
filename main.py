import discord
import yt_dlp
import asyncio


def bot_start():
    #Insira o token do bot abaixo
    TOKEN = ""

    intents = discord.Intents.default()
    intents.message_content = True

    bot = discord.Client(intents=intents)

    voz_client = {}

    yt_dl_options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto",
        "extractor_args": {"youtube": {"player_client": "web"}}
    }

    ytdl = yt_dlp.YoutubeDL(yt_dl_options)

    
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -filter:a "volume=0.25"'
    }

    @bot.event
    async def on_ready():
        print(f"{bot.user} está pronto para tocar!")
    
    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
        
        if message.content.startswith("!play"):
            if message.guild.id in voz_client and voz_client[message.guild.id].is_connected():
                voice_client=voz_client[message.guild.id]
            
            else:
                if not message.author.bot and message.author.voice and message.author.voice.channel:
                    voice_client = await message.author.voice.channel.connect()

                    voz_client[message.guild.id] = voice_client
                else:
                    await message.channel.send("Você não está em um canal de voz.")
                    return
            url=message.content.split()[1] 
            print(f"URL: {url}")

            loop = asyncio.get_event_loop()

            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

            if not data or "url" not in data:
                await message.channel.send("Não foi possível obter as informações da música.")
                return

            song = data["url"]

            player = discord.FFmpegOpusAudio(song, **ffmpeg_options)

            if voice_client.is_playing():
                voice_client.stop()
            
            voice_client.play(player)

            await message.channel.send(f"Tocando agora: {data.get('title', 'Música desconhecida')}")
        
        if message.content.startswith("!stop"):
            if message.guild.id in voz_client:
                voz_client[message.guild.id].stop()
                await voz_client[message.guild.id].disconnect()
                del voz_client[message.guild.id]

                await message.channel.send(f"Bot desconectado do canal de voz.")
    
    bot.run(TOKEN)

bot_start()