# main.py — کامل‌ترین بات Rust ایران (IRking 10X) | 100% کار می‌کنه در Railway
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Select, View
import yt_dlp as youtube_dl
import asyncio
from collections import deque
from datetime import datetime, timedelta
import os

# ==================== تنظیمات اولیه ====================
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
tree = bot.tree

# صف موزیک
music_queues = {}

# تنظیمات yt-dlp
ytdl = youtube_dl.YoutubeDL({
    'format': 'bestaudio/best',
    'noplaylist': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
})

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -filter:a "volume=0.5"'
}

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.title = data.get('title')

    @classmethod
    async def from_query(cls, query, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
            if 'entries' in data:
                data = data['entries'][0]
            return cls(discord.FFmpegPCMAudio(data['url'], **ffmpeg_options), data=data)
        except:
            return None

def play_next(interaction):
    guild_id = interaction.guild.id
    if guild_id in music_queues and music_queues[guild_id]:
        next_song = music_queues[guild_id].popleft()
        asyncio.run_coroutine_threadsafe(play_song(interaction, next_song), bot.loop)

async def play_song(interaction, query):
    player = await YTDLSource.from_query(query)
    if not player:
        return await interaction.followup.send("آهنگ پیدا نشد یا لینک اشتباهه!", ephemeral=True)
    interaction.guild.voice_client.play(player, after=lambda e: play_next(interaction))
    await interaction.followup.send(f"در حال پخش: **{player.title}**")

# ==================== دستورات اصلی (!prefix) ====================

@bot.command()
async def ip(ctx):
    embed = discord.Embed(title="آدرس سرور", description="```connect irkings.top```", color=0xff9900)
    embed.set_thumbnail(url="https://uploadkon.ir/uploads/f8c114_256b0e13495ed97b05b29e3481ef68f708.png")
    await ctx.send(embed=embed)

@bot.command()
async def cart(ctx):
    embed = discord.Embed(title="کارت به کارت", color=0xff9900)
    embed.add_field(name="شماره کارت", value="```6219-8618-1827-9068```", inline=False)
    embed.add_field(name="به نام", value="**فرهاد حسینی**", inline=False)
    embed.set_thumbnail(url="https://uploadkon.ir/uploads/f8c114_256b0e13495ed97b05b29e3481ef68f708.png")
    await ctx.send(embed=embed)

@bot.command()
async def wipe(ctx):
    now = datetime.now() + timedelta(hours=3, minutes=30)
    target = now.replace(hour=14, minute=0, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    if now.weekday() >= 3 and now >= target:
        target += timedelta(days=(7 - now.weekday()))
    remaining = target - now
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60
    embed = discord.Embed(title="تایمر وایپ بعدی", color=0x00ff00)
    embed.add_field(name="زمان وایپ", value="دوشنبه و پنج‌شنبه ساعت **14:00**", inline=False)
    embed.add_field(name="باقی‌مانده", value=f"{remaining.days} روز، {hours} ساعت و {minutes} دقیقه", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def developer(ctx, member: discord.Member = None):
    if not member:
        return await ctx.send("`!developer @یوزر`")
    role = discord.utils.get(ctx.guild.roles, name="Developer")
    if not role:
        role = await ctx.guild.create_role(name="Developer", color=discord.Color.gold(), hoist=True, mentionable=True)
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"بج Developer از {member.mention} برداشته شد")
    else:
        await member.add_roles(role)
        await ctx.send(f"بج Developer به {member.mention} داده شد!")

# ==================== دستور !shop کامل و بدون هیچ اروری ====================
@bot.command()
async def shop(ctx):
    select = Select(
        placeholder="رنک مورد نظرت رو انتخاب کن...",
        options=[
            discord.SelectOption(label="Legendary", value="legendary", emoji="🏆", description="ماه 360k | هفته 100k"),
            discord.SelectOption(label="Elite Commander", value="elite", emoji="💠", description="ماه 480k | هفته 120k"),
            discord.SelectOption(label="GameMaster", value="gamemaster", emoji="👑", description="ماه 640k | هفته 155k"),
            discord.SelectOption(label="Overlord", value="overlord", emoji="💎", description="ماه 800k | هفته 200k"),
        ]
    )

    async def callback(interaction):
        choice = interaction.data['values'][0]
        ranks = {
            "legendary": {
                "title": "رنک Legendary 🏆",
                "color": 0x00ff00,
                "price30": "360,000 تومان",
                "price7": "100,000 تومان",
                "perks": "• روشن کردن تورت\n• کیت مخصوص\n• افزایش سرعت آپگرید\n• mymini / myheli بدون کولداون\n• no cold & hot\n• reward بیشتر\n• بک‌پک بزرگتر",
                "images": [
                    "https://uploadkon.ir/uploads/dc8014_25Rust-11-14-2025-5-26-43-PM.png",
                    "https://uploadkon.ir/uploads/ca9c14_25Rust-11-14-2025-5-26-48-PM.png",
                    "https://uploadkon.ir/uploads/a05314_25Rust-11-14-2025-5-27-09-PM.png",
                    "https://uploadkon.ir/uploads/b4f414_25Rust-11-14-2025-5-27-14-PM.png",
                    "https://uploadkon.ir/uploads/c5ef14_25Rust-11-14-2025-5-27-18-PM.png",
                    "https://uploadkon.ir/uploads/06b714_25Rust-11-14-2025-5-27-23-PM.png"
                ]
            },
            "elite": {
                "title": "رنک Elite Commander 💠",
                "color": 0x00ffff,
                "price30": "480,000 تومان",
                "price7": "120,000 تومان",
                "perks": "• همه مزایای Legendary\n• کیت قوی‌تر\n• /back و /craft\n• هلیکوپتر شخصی\n• برداشت سنگ پخته",
                "images": [
                    "https://uploadkon.ir/uploads/b20714_25Rust-11-14-2025-5-26-05-PM.png",
                    "https://uploadkon.ir/uploads/a4c214_25Rust-11-14-2025-5-26-11-PM.png",
                    "https://uploadkon.ir/uploads/b67f14_25Rust-11-14-2025-5-26-15-PM.png",
                    "https://uploadkon.ir/uploads/b41614_25Rust-11-14-2025-5-26-20-PM.png",
                    "https://uploadkon.ir/uploads/d98014_25Rust-11-14-2025-5-26-25-PM.png"
                ]
            },
            "gamemaster": {
                "title": "رنک GameMaster 👑",
                "color": 0xffff00,
                "price30": "640,000 تومان",
                "price7": "155,000 تومان",
                "perks": "• همه مزایای Elite\n• بدون کولداون کیت\n• No Radiation & No Bleeding\n• هلیکوپتر و مینی دائمی",
                "images": [
                    "https://uploadkon.ir/uploads/420914_25Rust-11-14-2025-5-29-54-PM.png",
                    "https://uploadkon.ir/uploads/28fd14_25Rust-11-14-2025-5-29-58-PM.png",
                    "https://uploadkon.ir/uploads/3c7b14_25Rust-11-14-2025-5-30-04-PM.png",
                    "https://uploadkon.ir/uploads/af5614_25Rust-11-14-2025-5-30-07-PM.png",
                    "https://uploadkon.ir/uploads/245514_25Rust-11-14-2025-5-30-25-PM.png",
                    "https://uploadkon.ir/uploads/1c6714_25Rust-11-14-2025-5-30-30-PM.png"
                ]
            },
            "overlord": {
                "title": "رنک Overlord 💎",
                "color": 0xff00ff,
                "price30": "800,000 تومان",
                "price7": "200,000 تومان",
                "perks": "• همه چیز + نقش اختصاصی\n• تبلیغ دائمی سرور\n• دسترسی کامل ادمین\n• کیت اختصاصی دائمی",
                "images": [
                    "https://uploadkon.ir/uploads/603114_25Rust-11-14-2025-5-30-41-PM.png",
                    "https://uploadkon.ir/uploads/668c14_25Rust-11-14-2025-5-30-45-PM.png",
                    "https://uploadkon.ir/uploads/420614_25Rust-11-14-2025-5-30-51-PM.png",
                    "https://uploadkon.ir/uploads/b43c14_25Rust-11-14-2025-5-30-54-PM.png",
                    "https://uploadkon.ir/uploads/042d14_25Rust-11-14-2025-5-30-58-PM.png",
                    "https://uploadkon.ir/uploads/c20214_25Rust-11-14-2025-5-31-02-PM.png"
                ]
            }
        }

        data = ranks[choice]
        embed = discord.Embed(title=data["title"], color=data["color"])
        embed.add_field(name="۳۰ روز", value=data["price30"], inline=True)
        embed.add_field(name="۷ روز", value=data["price7"], inline=True)
        embed.add_field(name="مزایا", value=data["perks"], inline=False)
        embed.set_image(url=data["images"][0])
        embed.set_footer(text=f"عکس ۱ از {len(data['images'])} • برای خرید تیکت بزن")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        for i in range(1, len(data["images"])):
            emb = discord.Embed(color=data["color"])
            emb.set_image(url=data["images"][i])
            emb.set_footer(text=f"عکس {i+1} از {len(data['images'])}")
            await interaction.followup.send(embed=emb, ephemeral=True)

    select.callback = callback
    view = View(timeout=None)
    view.add_item(select)

    main_embed = discord.Embed(title="فروشگاه رنک IRking 10X", description="رنک مورد نظرت رو انتخاب کن:", color=0xff9900)
    main_embed.set_thumbnail(url="https://uploadkon.ir/uploads/f8c114_256b0e13495ed97b05b29e3481ef68f708.png")
    await ctx.send(embed=main_embed, view=view)

# ==================== دستورات موزیک (اسلش) ====================

@tree.command(name="join", description="بات وارد ویس چنل میشه")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        return await interaction.response.send_message("باید تو یه ویس چنل باشی!", ephemeral=True)
    channel = interaction.user.voice.channel
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(channel)
    else:
        await channel.connect()
    await interaction.response.send_message(f"وارد {channel.name} شدم!")

@tree.command(name="leave", description="بات از ویس خارج میشه")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        interaction.guild.voice_client.stop()
        music_queues.pop(interaction.guild.id, None)
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("خارج شدم!")
    else:
        await interaction.response.send_message("من تو ویس نیستم!", ephemeral=True)

@tree.command(name="play", description="آهنگ پخش کن یا به صف اضافه کن")
@app_commands.describe(query="اسم آهنگ یا لینک یوتیوب")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    if not interaction.guild.voice_client:
        if not interaction.user.voice:
            return await interaction.followup.send("اول باید تو ویس باشی!", ephemeral=True)
        await interaction.user.voice.channel.connect()

    guild_id = interaction.guild.id
    if guild_id not in music_queues:
        music_queues[guild_id] = deque()

    music_queues[guild_id].append(query)
    await interaction.followup.send(f"به صف اضافه شد: **{query}**")

    if not interaction.guild.voice_client.is_playing():
        play_next(interaction)

@tree.command(name="skip", description="آهنگ فعلی رو اسکیپ کن")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("اسکیپ شد!")
    else:
        await interaction.response.send_message("چیزی در حال پخش نیست!", ephemeral=True)

@tree.command(name="pause", description="پاز کردن موزیک")
async def pause(interaction: discord.Interaction):
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.pause()
        await interaction.response.send_message("پاز شد")
    else:
        await interaction.response.send_message("چیزی پخش نمیشه!", ephemeral=True)

@tree.command(name="resume", description="ادامه دادن موزیک")
async def resume(interaction: discord.Interaction):
    if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
        interaction.guild.voice_client.resume()
        await interaction.response.send_message("ادامه دادم")
    else:
        await interaction.response.send_message("موزیک پاز نیست!", ephemeral=True)

@tree.command(name="queue", description="نمایش صف موزیک")
async def queue_cmd(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id not in music_queues or not music_queues[guild_id]:
        return await interaction.response.send_message("صف خالیه!")
    songs = "\n".join([f"{i+1}. {song}" for i, song in enumerate(list(music_queues[guild_id])[:15])])
    await interaction.response.send_message(f"**صف موزیک:**\n{songs}")

# ==================== وضعیت چرخشی + تایمر وایپ ====================

async def status_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        await bot.change_presence(activity=discord.Game("connect irkings.top"))
        await asyncio.sleep(25)
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="IRking 10X 24/7"))
        await asyncio.sleep(20)

@tasks.loop(minutes=3)
async def wipe_announcer():
    now = datetime.now() + timedelta(hours=3, minutes=30)
    if now.weekday() in [0, 3] and now.hour == 14 and now.minute < 3:
        channel = bot.get_channel(1294698730834989128)  # ← اینجا ID چنل اعلانات رو بذار
        if channel:
            embed = discord.Embed(title="WIPE سرور وایپ شد!", color=0xff0000)
            embed.add_field(name="اتصال", value="`connect irkings.top`", inline=False)
            embed.set_image(url="https://uploadkon.ir/uploads/f8c114_256b0e13495ed97b05b29e3481ef68f708.png")
            await channel.send("@everyone", embed=embed)

@bot.event
async def on_ready():
    await tree.sync()
    bot.loop.create_task(status_loop())
    wipe_announcer.start()
    print(f"بات IRking 10X کامل و آنلاین شد | {bot.user}")

# ==================== اجرا ====================
bot.run(os.getenv("TOKEN"))
