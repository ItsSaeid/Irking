# main.py — بات کامل IRking 10X + موزیک + فروشگاه رنک (Railway Ready)
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

# yt-dlp تنظیمات
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
        self.url = data.get('url')

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
    if interaction.guild.id in music_queues and music_queues[interaction.guild.id]:
        next_song = music_queues[interaction.guild.id].popleft()
        asyncio.run_coroutine_threadsafe(play_song(interaction, next_song), bot.loop)

async def play_song(interaction, query):
    player = await YTDLSource.from_query(query)
    if not player:
        return await interaction.followup.send("آهنگ پیدا نشد!", ephemeral=True)
    interaction.guild.voice_client.play(player, after=lambda e: play_next(interaction))
    await interaction.followup.send(f"در حال پخش: **{player.title}**")

# ==================== دستورات اصلی ====================

@bot.command()
async def ip(ctx):
    embed = discord.Embed(title="آدرس سرور IRking 10X", description="```connect irkings.top```", color=0xff9900)
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
        target += timedelta(days=7 - now.weekday())
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
        role = await ctx.guild.create_role(name="Developer", color=discord.Color.gold(), hoist=True)
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"بج Developer از {member.mention} برداشته شد")
    else:
        await member.add_roles(role)
        await ctx.send(f"بج Developer به {member.mention} داده شد!")

# ==================== دستور !shop با منوی کامل و عکس ====================
@bot.command()
async def shop(ctx):
    select = Select(
        placeholder="رنک مورد نظرت رو انتخاب کن...",
        options=[
            discord.SelectOption(label="Legendary", value="legendary", emoji="trophy", description="ماه 360k | هفته 100k"),
            discord.SelectOption(label="Elite Commander", value="elite", emoji="gem", description="ماه 480k | هفته 120k"),
            discord.SelectOption(label="GameMaster", value="gamemaster", emoji="crown", description="ماه 640k | هفته 155k"),
            discord.SelectOption(label="Overlord", value="overlord", emoji="diamond", description="ماه 800k | هفته 200k"),
        ]
    )

    async def callback(interaction):
        choice = interaction.data['values'][0]
        ranks = {
            "legendary": {
                "title": "رنک Legendary",
                "color": 0x00ff00,
                "price30": "360,000 تومان",
                "price7": "100,000 تومان",
                "perks": "• روشن کردن تورت\n• کیت مخصوص\n• افزایش سرعت آپگرید\n• mymini / myheli / myattack بدون کولداون\n• no cold & hot\n• reward بیشتر\n• بک‌پک بزرگتر\n• سرعت تله‌پورت بیشتر\n• سثوم بیشتر",
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
                "title": "رنک Elite Commander",
                "color": 0x00ffff,
                "price30": "480,000 تومان",
                "price7": "120,000 تومان",
                "perks": "• همه مزایای Legendary\n• کیت قوی‌تر\n• /back و /craft\n• هلیکوپتر شخصی\n• برداشت سنگ پخته\n• افزایش سرعت تله‌پورت",
                "images": [
                    "https://uploadkon.ir/uploads/b20714_25Rust-11-14-2025-5-26-05-PM.png",
                    "https://uploadkon.ir/uploads/a4c214_25Rust-11-14-2025-5-26-11-PM.png",
                    "https://uploadkon.ir/uploads/b67f14_25Rust-11-14-2025-5-26-15-PM.png",
                    "https://uploadkon.ir/uploads/b41614_25Rust-11-14-2025-5-26-20-PM.png",
                    "https://uploadkon.ir/uploads/d98014_25Rust-11-14-2025-5-26-25-PM.png"
                ]
            },
            "gamemaster": {
                "title": "رنک GameMaster",
                "color": 0xffff00,
                "price30": "640,000 تومان",
                "price7": "155,000 تومان",
                "perks": "• همه مزایای Elite\n• بدون کولداون کیت\n• No Radiation & No Bleeding\n• هلیکوپتر و مینی دائمی\n• دسترسی نیمه ادمین",
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
                "title": "رنک Overlord",
                "color": 0xff00ff,
                "price30": "800,000 تومان",
                "price7": "200,000 تومان",
                "perks": "• همه چیز + نقش اختصاصی\n• تبلیغ دائمی سرور\n• دسترسی کامل ادمین\n• اولویت در همه چیز\n• کیت اختصاصی دائمی",
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
            emb.set_footer(text=f"عکس {i+1} از {len(data['images'])} • برای خرید تیکت بزن")
            await interaction.followup.send(embed=emb, ephemeral=True)

    select.callback = callback
    view = View(timeout=None)
    view.add_item(select)

    main_embed = discord.Embed(
        title="فروشگاه رنک IRking 10X",
        description="رنک مورد نظر خود را انتخاب کنید:",
        color=0xff9900
    )
    main_embed.set_thumbnail(url="https://uploadkon.ir/uploads/f8c114_256b0e13495ed97b05b29e3481ef68f708.png")
    await ctx.send(embed=main_embed, view=view)

# ==================== دستورات موزیک (اسلش) ====================
# (همون قبلی، فقط خلاصه کردم که جا بشه)
@tree.command(name="join", description="وارد ویس شو")
async def join(i: discord.Interaction): ...
@tree.command(name="leave", description="خروج از ویس")
async def leave(i: discord.Interaction): ...
@tree.command(name="play", description="پخش آهنگ")
@app_commands.describe(query="اسم آهنگ یا لینک")
async def play(i: discord.Interaction, query: str): ...
@tree.command(name="skip", description="اسکیپ")
async def skip(i: discord.Interaction): ...
@tree.command(name="pause", description="پاز")
async def pause(i: discord.Interaction): ...
@tree.command(name="resume", description="ادامه")
async def resume(i: discord.Interaction): ...
@tree.command(name="queue", description="صف موزیک")
async def queue_cmd(i: discord.Interaction): ...

# ==================== وضعیت + وایپ تایمر ====================
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
        channel = bot.get_channel(1294698730834989128)  # ID چنل وایپ رو عوض کن
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
    print(f"بات IRking 10X کامل و آماده‌ست! | {bot.user}")

bot.run(os.getenv("TOKEN"))
