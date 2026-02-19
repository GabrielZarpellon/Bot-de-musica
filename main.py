import discord
import yt_dlp
import asyncio


def bot_start():
    TOKEN = ""

    intents = discord.Intents.default()
    intents.message_content = True

    bot = discord.Client(intents=intents)

    voz_client = {}
    filas = {}

    yt_dl_options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "default_search": "auto",
    }

    ytdl = yt_dlp.YoutubeDL(yt_dl_options)

    ffmpeg_options = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn -filter:a volume=0.25"
    }

    # ---------------- FUNÇÃO PARA TOCAR PRÓXIMA ----------------
    async def tocar_proxima(guild_id):
        if filas[guild_id]:
            musica = filas[guild_id].pop(0)
            voice_client = voz_client[guild_id]

            player = discord.FFmpegOpusAudio(musica["url"], **ffmpeg_options)

            def after_playing(error):
                fut = tocar_proxima(guild_id)
                asyncio.run_coroutine_threadsafe(fut, bot.loop)

            voice_client.play(player, after=after_playing)

            canal = musica["canal"]
            await canal.send(f"🎵 Tocando agora: {musica['titulo']}")
        else:
            await voz_client[guild_id].disconnect()
            del voz_client[guild_id]

    @bot.event
    async def on_ready():
        print(f"{bot.user} está pronto!")

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        # ---------------- PLAY ----------------
        if message.content.startswith("!play"):

            if len(message.content.split()) < 2:
                await message.channel.send("Use: !play <nome ou url>")
                return

            if not message.author.voice:
                await message.channel.send("Você precisa estar em um canal de voz.")
                return

            guild_id = message.guild.id

            if guild_id not in filas:
                filas[guild_id] = []

            if guild_id not in voz_client or not voz_client[guild_id].is_connected():
                voice_client = await message.author.voice.channel.connect()
                voz_client[guild_id] = voice_client
            else:
                voice_client = voz_client[guild_id]

            url = message.content.split(maxsplit=1)[1]

            await message.channel.send("🔎 Buscando música...")

            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(url, download=False)
            )

            if "entries" in data:
                data = data["entries"][0]

            musica = {
                "url": data["url"],
                "titulo": data["title"],
                "canal": message.channel
            }

            if voice_client.is_playing():
                filas[guild_id].append(musica)
                await message.channel.send(
                    f"📜 Adicionada à fila: {musica['titulo']}"
                )
            else:
                filas[guild_id].append(musica)
                await tocar_proxima(guild_id)

        # ---------------- SKIP ----------------
        if message.content.startswith("!skip"):
            guild_id = message.guild.id
            if guild_id in voz_client and voz_client[guild_id].is_playing():
                voz_client[guild_id].stop()
                await message.channel.send("⏭️ Música pulada.")

        # ---------------- STOP ----------------
        if message.content.startswith("!stop"):
            guild_id = message.guild.id
            if guild_id in voz_client:
                filas[guild_id].clear()
                voz_client[guild_id].stop()
                await voz_client[guild_id].disconnect()
                del voz_client[guild_id]
                await message.channel.send("🛑 Fila limpa e bot desconectado.")

        # ---------------- FILA ----------------
        if message.content.startswith("!fila"):
            guild_id = message.guild.id
            if guild_id in filas and filas[guild_id]:
                lista = "\n".join(
                    [f"{i+1}. {m['titulo']}" for i,
                        m in enumerate(filas[guild_id])]
                )
                await message.channel.send(f"📜 Fila atual:\n{lista}")
            else:
                await message.channel.send("A fila está vazia.")

    bot.run(TOKEN)


bot_start()
