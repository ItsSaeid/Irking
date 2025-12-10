# main.py
import discord
from discord.ext import commands, tasks
from discord.ui import Select, View, Button  # ← اینجا Button اضافه شد
from datetime import datetime, timedelta
import asyncio
import io
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# ==================== تنظیمات سیستم تیکت ====================
TICKET_CATEGORY_NAME = "TICKETS"
LOG_CHANNEL_ID = 1445905705323335680
TRANSCRIPT_CHANNEL_ID = 1445905705323335680
STAFF_ROLE_ID = 0  # آیدی رول استاف

# --------------------- Ticket Select ---------------------
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="باگ", description="Bug", emoji="⚙️"),
            discord.SelectOption(label="ریپورت بازیکن", description="Cheat", emoji="⚠️"),
            discord.SelectOption(label="خرید از شاپ", description="Shop", emoji="🛍️"),
            discord.SelectOption(label="درخواست رنک استریمر", description="Streamer", emoji="🎥"),
        ]
        super().__init__(
            placeholder="دسته‌بندی تیکت را انتخاب کنید...",
            options=options,
            custom_id="ticket_category"
        )

    async def callback(self, interaction: discord.Interaction):
        category = discord.utils.get(interaction.guild.categories, name=TICKET_CATEGORY_NAME)
        if not category:
            return await interaction.response.send_message("دسته تیکت پیدا نشد!", ephemeral=True)

        ticket_num = len([c for c in category.channels if c.name.startswith("ticket-")]) + 1
        channel_name = f"ticket-{ticket_num:04d}-{interaction.user.name}"

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        for role in interaction.guild.roles:
            if role.permissions.manage_messages:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"User: {interaction.user} | ID: {interaction.user.id}"
        )

        await interaction.response.send_message(f"تیکت ساخته شد! {channel.mention}", ephemeral=True)

        embed = discord.Embed(
            title="🎫 تیکت جدید",
            description=f"**دسته:** {self.values[0]}\n**کاربر:** {interaction.user.mention}",
            color=0x00ff99,
            timestamp=datetime.now().astimezone()
        )

        view = TicketControlView()
        await channel.send(
            f"{interaction.user.mention} | <@&{STAFF_ROLE_ID}>",
            embed=embed,
            view=view
        )

class TicketSelectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# --------------------- Close Ticket Function ---------------------
async def close_ticket(channel, closed_by):
    embed = discord.Embed(
        title="در حال بستن تیکت...",
        description="تیکت در ۵ ثانیه آینده بسته و آرشیو می‌شود.",
        color=0xff0000
    )
    await channel.send(embed=embed)

    messages = [msg async for msg in channel.history(limit=None, oldest_first=True)]
    transcript = "<html><body><h1>Transcript</h1><ul>"
    for msg in messages:
        time = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        transcript += f"<li><b>{msg.author}</b> - {time}: {msg.content}</li>"
        for a in msg.attachments:
            transcript += f"<br><a href='{a.url}'>Attachment</a>"
    transcript += "</ul></body></html>"

    transcript_file = discord.File(
        io.BytesIO(transcript.encode("utf-8")),
        filename=f"{channel.name}.html"
    )

    log = bot.get_channel(TRANSCRIPT_CHANNEL_ID)
    if log:
        await log.send(
            f"📁 **تیکت بسته شد**\n**بسته شده توسط:** {closed_by}\n**چنل:** {channel.name}",
            file=transcript_file
        )

    await asyncio.sleep(5)
    await channel.delete()

# --------------------- Ticket Controls ---------------------
class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="بستن",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="close_ticket_button"
    )
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        await close_ticket(interaction.channel, interaction.user)

# ==================== دستورات CMD ====================
@bot.command()
@commands.has_permissions(administrator=True)
async def ticketpanel(ctx):
    embed = discord.Embed(
        title="🎫 سیستم تیکت",
        description="دسته‌بندی مورد نظر را انتخاب کنید.",
        color=0xff0066,
        timestamp=datetime.now().astimezone()
    )
    view = TicketSelectView()
    await ctx.send(embed=embed, view=view)

@bot.command()
async def ip(ctx):
    embed = discord.Embed(title="آدرس سرور", description="```connect irkings.top```", color=0xff9900)
    await ctx.send(embed=embed)

@bot.command()
async def cart(ctx):
    embed = discord.Embed(title="کارت به کارت", color=0xff9900)
    embed.add_field(name="شماره کارت", value="```6219-8618-1827-9068```", inline=False)
    embed.add_field(name="به نام", value="**فرهاد حسینی**", inline=False)
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

# ==================== دستور !shop ====================
# ------------------- دستور !shop کامل -------------------
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
                "perks": "• روشن کردن تورت\n• کیت مخصوص\n• افزایش سرعت آپگرید\n• mymini / myheli بدون کولداون\n• no cold & hot\n• reward بیشتر\n• بک‌پک بزرگتر بیلد کردت پیشرفته ساختن تورت راکتی برداشتن سنگ پخته",
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
                "perks": "• روشن کردن تورت\n• کیت مخصوص\n• افزایش سرعت آپگرید\n• mymini / myheli بدون کولداون\n• no cold & hot\n• reward بیشتر\n• بک‌پک بزرگتر بیلد کردن پیشرفته تورت راکتی",
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

# ——————————————————— دستور !vote ———————————————————
@bot.command()
@commands.has_permissions(administrator=True)
async def vote(ctx, *, text=None):
    if not text:
        return await ctx.send("`!vote سوال (اختیاری: زمان 24h و لینک عکس)`")

    image_url = None
    duration = 86400  # 24 ساعت پیش‌فرض
    question = text.strip()

    # تشخیص زمان
    time_match = re.search(r"(\d+)([hmd])", question.lower())
    if time_match:
        num = int(time_match.group(1))
        unit = time_match.group(2)
        if unit == 'h': duration = num * 3600
        elif unit == 'm': duration = num * 60
        elif unit == 'd': duration = num * 86400
        question = re.sub(r"\d+[hmd]\s*", "", question, count=1).strip()

    # تشخیص لینک عکس
    url_match = re.search(r"(https?://\S+\.(?:png|jpg|jpeg|gif|webp))", text)
    if url_match:
        image_url = url_match.group(1)
        question = question.replace(url_match.group(1), "").strip()

    if not question:
        question = "نظرسنجی"

    embed = discord.Embed(
        title="نظرسنجی",
        description=f"**{question}**",
        color=0x5865f2,
        timestamp=datetime.utcnow() + timedelta(seconds=duration)
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url or None)
    if image_url:
        embed.set_image(url=image_url)
    embed.add_field(name="آره ✅", value="0 رای", inline=True)
    embed.add_field(name="نه ❌", value="0 رای", inline=True)
    embed.set_footer(text=f"پایان: ‎")

    view = VoteView()
    msg = await ctx.send(embed=embed, view=view)

    votes[msg.id] = {
        "yes": 0,
        "no": 0,
        "voters": set(),
        "end": datetime.utcnow() + timedelta(seconds=duration),
        "msg": msg
    }

class VoteView(View):
    def __init__(self):
        super().__init__(timeout=None)

    async def update(self, interaction):
        data = votes.get(interaction.message.id)
        if not data: return

        total = data["yes"] + data["no"]
        yes_p = int(data["yes"] / total * 100) if total > 0 else 0
        no_p = 100 - yes_p

        bar = "🟩" * int(yes_p / 10) + "⬜" * (10 - int(yes_p / 10))

        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name=f"آره ✅ ({yes_p}%)", value=f"{bar} {data['yes']} رای", inline=True)
        embed.set_field_at(1, name=f"نه ❌ ({no_p}%)", value=f"{bar[::-1] if no_p > yes_p else '⬜'*10} {data['no']} رای", inline=True)

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="آره", style=discord.ButtonStyle.green, emoji="✅", custom_id="yes_vote_2025")
    async def yes(self, interaction):
        data = votes.get(interaction.message.id)
        if not data or interaction.user.id in data["voters"]:
            return await interaction.response.send_message("قبلاً رای دادی!", ephemeral=True)
        data["yes"] += 1
        data["voters"].add(interaction.user.id)
        await self.update(interaction)

    @discord.ui.button(label="نه", style=discord.ButtonStyle.red, emoji="❌", custom_id="no_vote_2025")
    async def no(self, interaction):
        data = votes.get(interaction.message.id)
        if not data or interaction.user.id in data["voters"]:
            return await interaction.response.send_message("قبلاً رای دادی!", ephemeral=True)
        data["no"] += 1
        data["voters"].add(interaction.user.id)
        await self.update(interaction)

@bot.event
async def on_ready():
    print(f"بات {bot.user} آنلاین شد!")
    
    # ←←← این خط جدیده، فقط اینو اضافه کن
    activity = discord.Game(name="connect irkings.top")
    await bot.change_presence(status=discord.Status.online, activity=activity)

# دستور !say — هر متنی که بنویسی رو بات می‌فرسته (خام و بدون ریپلای)
@bot.command(name="say")
@commands.has_permissions(administrator=True)
async def say(ctx, *, text=None):
    if not text:
        return
    try:
        await ctx.message.delete()
    except:
        pass
    await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())


# ==================== Run ====================
bot.run(os.getenv("TOKEN"))
