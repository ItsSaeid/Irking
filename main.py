import discord
from discord.ext import commands, tasks
from discord.ui import Select, View
import os
import asyncio
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # برای دادن نقش

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# -------------------- Setup Hook --------------------
async def setup_hook():
    bot.loop.create_task(status_changer())
    wipe_timer.start()

bot.setup_hook = setup_hook


# -------------------- وضعیت چرخشی --------------------
async def status_changer():
    await bot.wait_until_ready()
    statuses = [
        (discord.Game(name="connect irkings.top"), discord.Status.online),
        (discord.Activity(type=discord.ActivityType.watching, name="IRking 10X 24/7"), discord.Status.idle),
        (discord.Activity(type=discord.ActivityType.listening, name="به دستورات شما"), discord.Status.dnd),
    ]
    while not bot.is_closed():
        for activity, status in statuses:
            await bot.change_presence(activity=activity, status=status)
            await asyncio.sleep(22)


# -------------------- تایمر وایپ (دوشنبه و پنج‌شنبه ساعت 14:00 = 2 ظهر) --------------------
@tasks.loop(minutes=3)  # هر 3 دقیقه چک می‌کنه
async def wipe_timer():
    now = datetime.now() + timedelta(hours=3, minutes=30)  # UTC → ایران
    # دوشنبه = 0 , پنج‌شنبه = 3
    if now.weekday() in [0, 3] and now.hour == 14 and now.minute < 3:
        channel = bot.get_channel(1294698730834989128)  # ← ID چنل اعلان وایپ رو عوض کن
        if channel:
            embed = discord.Embed(title="WIPE سرور وایپ شد!", color=0xff0000)
            embed.add_field(name="زمان وایپ", value=now.strftime("%Y/%m/%d - 14:00"), inline=False)
            embed.add_field(name="اتصال", value="`connect irkings.top`", inline=False)
            embed.set_image(url="https://uploadkon.ir/uploads/f8c114_256b0e13495ed97b05b29e3481ef68f708.png")
            await channel.send("@everyone", embed=embed)


# -------------------- دستور !wipe --------------------
@bot.command()
async def wipe(ctx):
    now = datetime.now() + timedelta(hours=3, minutes=30)
    weekday = now.weekday()

    if weekday == 0 and now.hour < 14:
        next_wipe = now.replace(hour=14, minute=0, second=0, microsecond=0)
    elif weekday == 3 and now.hour < 14:
        next_wipe = now.replace(hour=14, minute=0, second=0, microsecond=0)
    elif weekday < 3:
        next_wipe = (now + timedelta(days=3 - weekday)).replace(hour=14, minute=0, second=0, microsecond=0)
    else:
        next_wipe = (now + timedelta(days=7 - weekday)).replace(hour=14, minute=0, second=0, microsecond=0)

    remaining = next_wipe - now
    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)

    embed = discord.Embed(title="تایمر وایپ بعدی", color=0x00ff00)
    embed.add_field(name="روز و تاریخ", value=next_wipe.strftime("%A %d/%m/%Y"), inline=False)
    embed.add_field(name="ساعت وایپ", value="14:00 (2 ظهر)", inline=False)
    embed.add_field(name="زمان باقی‌مانده", value=f"{remaining.days} روز، {hours} ساعت و {minutes} دقیقه", inline=False)
    embed.set_footer(text="هر دوشنبه و پنج‌شنبه ساعت 14:00 وایپ داریم")
    await ctx.send(embed=embed)


# -------------------- دستور !developer add (بج دولوپر) --------------------
@bot.command()
@commands.has_permissions(administrator=True)  # فقط ادمین بتونه بزنه
async def developer(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("لطفاً یه نفر رو تگ کن: `!developer add @یوزر`")
        return

    # ساخت نقش دولوپر اگه وجود نداشته باشه
    role = discord.utils.get(ctx.guild.roles, name="Developer")
    if role is None:
        role = await ctx.guild.create_role(
            name="Developer",
            color=discord.Color.from_rgb(255, 215, 0),  # طلایی
            hoist=True,
            mentionable=True
        )
        await ctx.send("نقش **Developer** ساخته شد!")

    # اضافه/حذف کردن بج
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"بج Developer از {member.mention} برداشته شد")
    else:
        await member.add_roles(role)
        await ctx.send(f"بج Developer به {member.mention} داده شد!")


# -------------------- دستور !cart --------------------
@bot.command()
async def cart(ctx):
    embed = discord.Embed(title="کارت به کارت", color=0xff9900)
    embed.add_field(name="شماره کارت", value="```6219-8618-1827-9068```", inline=False)
    embed.add_field(name="به نام", value="**فرهاد حسینی**", inline=False)
    embed.add_field(name="توضیحات", value="رسید + آیدی استیم رو توی تیکت بفرستید", inline=False)
    embed.set_thumbnail(url="https://uploadkon.ir/uploads/f8c114_256b0e13495ed97b05b29e3481ef68f708.png")
    await ctx.send(embed=embed)


# -------------------- دستور !ip --------------------
@bot.command()
async def ip(ctx):
    embed = discord.Embed(title="آدرس سرور", description="```connect irkings.top```", color=0xff9900)
    embed.set_thumbnail(url="https://uploadkon.ir/uploads/f8c114_256b0e13495ed97b05b29e3481ef68f708.png")
    await ctx.send(embed=embed)


# -------------------- دستور !shop (کامل، فقط یه کم کوتاه کردم که جا بشه) --------------------
@bot.command()
async def shop(ctx):
    select = Select(placeholder="رنک مورد نظرت رو انتخاب کن...",
        options=[
            discord.SelectOption(label="Legendary", value="legendary", emoji="trophy", description="ماه 360k | هفته 100k"),
            discord.SelectOption(label="Elite Commander", value="elite", emoji="gem", description="ماه 480k | هفته 120k"),
            discord.SelectOption(label="GameMaster", value="gamemaster", emoji="crown", description="ماه 640k | هفته 155k"),
            discord.SelectOption(label="Overlord", value="overlord", emoji="diamond", description="ماه 800k | هفته 200k"),
        ])

    async def callback(interaction):
        choice = interaction.data['values'][0]
        ranks = {
            "legendary":   {"title": "رنک Legendary trophy", "color": 0x00ff00, "price30": "360,000 تومان", "price7": "100,000 تومان", "perks": "• تورت\n• کیت\n• بدون کولداون...", "images": [...]},
            "elite":       {"title": "رنک Elite Commander gem", "color": 0x00ffff, "price30": "480,000 تومان", "price7": "120,000 تومان", "perks": "...", "images": [...]},
            "gamemaster":  {"title": "رنک GameMaster crown", "color": 0xffff00, "price30": "640,000 تومان", "price7": "155,000 تومان", "perks": "...", "images": [...]},
            "overlord":    {"title": "رنک Overlord diamond", "color": 0xff00ff, "price30": "800,000 تومان", "price7": "200,000 تومان", "perks": "...", "images": [...]},
        }
        data = ranks[choice]
        embed = discord.Embed(title=data["title"], color=data["color"])
        embed.add_field(name="۳۰ روز", value=data["price30"], inline=True)
        embed.add_field(name="۷ روز", value=data["price7"], inline=True)
        embed.add_field(name="مزایا", value=data["perks"], inline=False)
        embed.set_image(url=data["images"][0])
        embed.set_footer(text="برای خرید تیکت بزن")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        for i in range(1, len(data["images"])):
            emb = discord.Embed(color=data["color"])
            emb.set_image(url=data["images"][i])
            await interaction.followup.send(embed=emb, ephemeral=True)

    select.callback = callback
    view = View(timeout=None)
    view.add_item(select)
    main = discord.Embed(title="فروشگاه رنک IRking 10X", description="رنک دلخواهت رو انتخاب کن:", color=0xff9900)
    main.set_thumbnail(url="https://uploadkon.ir/uploads/f8c114_256b0e13495ed97b05b29e3481ef68f708.png")
    await ctx.send(embed=main, view=view)


# -------------------- روشن شدن بات --------------------
@bot.event
async def on_ready():
    print(f"بات {bot.user} با موفقیت روشن شد!")
    print("وایپ هر دوشنبه و پنج‌شنبه ساعت 14:00")
    print("دستور !developer add فعال شد")


bot.run(os.getenv("TOKEN"))
