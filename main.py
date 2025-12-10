# main.py — نسخه نهایی و کامل (فقط کپی کن و اجرا کن)

import discord
from discord.ext import commands
from discord.ui import Select, View, Button
import asyncio
import io
import os
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# تنظیمات
TICKET_CATEGORY_NAME = "TICKETS"
TRANSCRIPT_CHANNEL_ID = 1445905705323335680  # چنل آرشیو ترانسکریپت
STAFF_ROLE_ID = 0  # اگه رول استاف داری بذار، وگرنه 0

# ذخیره نظرسنجی‌ها
votes = {}

# ——————————————————— تیکت سیستم ———————————————————
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="باگ", emoji="Gear", description="گزارش باگ"),
            discord.SelectOption(label="ریپورت بازیکن", emoji="Warning", description="ریپورت چیت/توهین"),
            discord.SelectOption(label="خرید از شاپ", emoji="Shopping Bags", description="مشکل پرداخت"),
            discord.SelectOption(label="درخواست رنک استریمر", emoji="Video Camera", description="اپلای استریمر"),
        ]
        super().__init__(placeholder="دسته‌بندی تیکت را انتخاب کنید...", options=options, custom_id="ticket_select")

    async def callback(self, interaction: discord.Interaction):
        category = discord.utils.get(interaction.guild.categories, name=TICKET_CATEGORY_NAME) or await interaction.guild.create_category(TICKET_CATEGORY_NAME)
        count = len([c for c in category.text_channels if c.name.startswith("ticket-")]) + 1
        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{count:04d}",
            category=category,
            overwrites={
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
            }
        )
        for role in interaction.guild.roles:
            if role.permissions.manage_messages:
                await channel.set_permissions(role, read_messages=True)

        await interaction.response.send_message(f"تیکت ساخته شد {channel.mention}", ephemeral=True)
        await channel.send("@here", embed=discord.Embed(title="تیکت جدید", description=f"دسته: {self.values[0]}", color=0x00ff99), view=CloseView())

class TicketSelectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="بستن تیکت", style=discord.ButtonStyle.danger, emoji="Lock", custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        transcript = "<html><body><h2>تیکت بسته شد</h2><ol>"
        async for msg in interaction.channel.history(oldest_first=True):
            transcript += f"<li><b>{msg.author}</b>: {discord.utils.escape_markdown(msg.content)}</li>"
        transcript += "</ol></body></html>"
        file = discord.File(io.BytesIO(transcript.encode()), f"{interaction.channel.name}.html")
        log = bot.get_channel(TRANSCRIPT_CHANNEL_ID)
        if log:
            await log.send(f"بسته شده توسط {interaction.user.mention}", file=file)
        await interaction.followup.send("تیکت بسته شد...", ephemeral=True)
        await asyncio.sleep(3)
        await interaction.channel.delete()

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


# ——————————————————— !say ———————————————————
@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, *, text=None):
    if not text:
        return await ctx.send("یه چیزی بنویس بعدش!")

    await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())



votes = {}

@bot.command()
@commands.has_permissions(administrator=True)
async def vote(ctx, *, args=None):
    if not args:
        return await ctx.send("`!vote سوال | زمان (مثلاً 100h) | عکس`")

    # جدا کردن زمان و عکس
    import re
    duration = 86400  # پیش‌فرض 24 ساعت
    image_url = None
    question = args

    # زمان (مثلاً 100h)
    time_match = re.search(r"(\d+)([hmd])", args.lower())
    if time_match:
        num = int(time_match.group(1))
        unit = time_match.group(2)
        if unit == 'h': duration = num * 3600
        elif unit == 'm': duration = num * 60
        elif unit == 'd': duration = num * 86400
        question = re.sub(r"\d+[hmd]\s*", "", question, count=1).strip()

    # عکس
    url_match = re.search(r"(https?://\S+\.(?:png|jpg|jpeg|gif|webp))", args)
    if url_match:
        image_url = url_match.group(1)
        question = question.replace(image_url, "").strip()

    if not question.strip():
        return await ctx.send("سوال رو بنویس!")

    end_time = datetime.utcnow() + timedelta(seconds=duration)

    embed = discord.Embed(
        title="نظرسنجی جدید",
        description=f"**{question}**",
        color=0x00ffff,
        timestamp=end_time
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url or None)
    if image_url:
        embed.set_image(url=image_url)
    embed.add_field(name="آره", value="0 رای", inline=True)
    embed.add_field(name="نه", value="0 رای", inline=True)
    embed.set_footer(text=f"زمان باقی‌مونده: {duration//3600}h")

    view = VoteView()
    msg = await ctx.send(embed=embed, view=view)

    votes[msg.id] = {"yes":0, "no":0, "voters":set()}

class VoteView(View):
    def __init__(self):
        super().__init__(timeout=None)

    async def update(self, interaction):
        data = votes.get(interaction.message.id)
        if not data: return
        total = data["yes"] + data["no"]
        yes_p = int(data["yes"]/total*100) if total else 0
        no_p = 100 - yes_p
        yes_bar = "🟩"* (yes_p//10) + "⬜"*(10-yes_p//10)
        no_bar = "🟥"* (no_p//10) + "⬜"*(10-no_p//10)

        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name=f"آره ({yes_p}%)", value=f"{yes_bar} {data['yes']} رای", inline=True)
        embed.set_field_at(1, name=f"نه ({no_p}%)", value=f"{no_bar} {data['no']} رای", inline=True)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="آره", style=discord.ButtonStyle.green, emoji="Check Mark Button", custom_id="v_yes_2025")
    async def yes(self, interaction):
        data = votes.get(interaction.message.id)
        if data and interaction.user.id not in data["voters"]:
            data["yes"] += 1
            data["voters"].add(interaction.user.id)
            await self.update(interaction)
        else:
            await interaction.response.send_message("قبلاً رای دادی!", ephemeral=True)

    @discord.ui.button(label="نه", style=discord.ButtonStyle.red, emoji="Cross Mark", custom_id="v_no_2025")
    async def no(self, interaction):
        data = votes.get(interaction.message.id)
        if data and interaction.user.id not in data["voters"]:
            data["no"] += 1
            data["voters"].add(interaction.user.id)
            await self.update(interaction)
        else:
            await interaction.response.send_message("قبلاً رای دادی!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"بات {bot.user} آنلاین شد!")
    await bot.change_presence(activity=discord.Game("connect irkings.top"))
    bot.add_view(VoteView())  # بدون این خط کار نمی‌کنه!

# ——————————————————— دستورات دیگر ———————————————————
@bot.command()
async def ip(ctx):
    await ctx.send(embed=discord.Embed(title="آدرس سرور", description="```connect irkings.top```", color=0xff9900))

giveaways = {}

@bot.command()
@commands.has_permissions(administrator=True)
async def giveaway(ctx, time: str, winners: int, *, prize: str):
    # تبدیل زمان
    try:
        if time.endswith('s'): secs = int(time[:-1])
        elif time.endswith('m'): secs = int(time[:-1]) * 60
        elif time.endswith('h'): secs = int(time[:-1]) * 3600
        elif time.endswith('d'): secs = int(time[:-1]) * 86400
        else: raise ValueError
    except:
        return await ctx.send("زمان اشتباه! مثال: `1h` `30m` `2d`")

    end_time = datetime.utcnow() + timedelta(seconds=secs)

    embed = discord.Embed(
        title="جایزه ویژه!",
        description=f"**{prize}**\n\nبرای شرکت روی دکمه بزنید\nبرنده‌ها: **{winners} نفر**\nزمان باقی‌مونده: **{time}**",
        color=0xff9f00,
        timestamp=end_time
    )
    embed.set_thumbnail(url="https://i.imgur.com/2Z2yM9c.gif")
    embed.set_footer(text="شرکت کرده: 0 نفر")

    view = GiveawayView()
    message = await ctx.send(embed=embed, view=view)

    giveaways[message.id] = {
        "end": end_time,
        "winners": winners,
        "prize": prize,
        "entries": [],
        "message": message
    }

class GiveawayView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="شرکت در گیواوی", style=discord.ButtonStyle.blurple, emoji="Party Popper", custom_id="gw_join_2025")
    async def join(self, interaction: discord.Interaction, button: Button):
        gw = giveaways.get(interaction.message.id)
        if not gw:
            return

        if interaction.user.id in gw["entries"]:
            return await interaction.response.send_message("قبلاً شرکت کردی!", ephemeral=True)

        gw["entries"].append(interaction.user.id)

        embed = interaction.message.embeds[0]
        embed.set_footer(text=f"شرکت کرده: {len(gw['entries'])} نفر")
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        gw = giveaways.get(self.message.id)
        if not gw or not gw["entries"]:
            await self.message.edit(content="گیواوی لغو شد — کسی شرکت نکرد", embed=None, view=None)
            return

        import random
        winners = random.sample(gw["entries"], k=min(gw["winners"], len(gw["entries"])))
        mention = " ".join([f"<@{u}>" for u in winners])

        await self.message.edit(
            content=f"گیواوی تموم شد!\nبرنده‌ها: {mention}\nجایزه: **{gw['prize']}**",
            embed=None,
            view=None
        )
        await self.message.reply(f"تبریک به برنده‌ها! {mention}")
# ——————————————————— آماده شدن بات ———————————————————
@bot.event
async def on_ready():
    print(f"بات {bot.user} آنلاین شد!")
    await bot.change_presence(activity=discord.Game("connect irkings.top"))
    bot.add_view(TicketSelectView())
    bot.add_view(CloseView())
    bot.add_view(VoteView())

# ——————————————————— اجرا ———————————————————
bot.run(os.getenv("TOKEN"))
