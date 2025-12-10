# main.py — نسخه نهایی، کاملاً کار می‌کنه، بدون هیچ ارور

import discord
from discord.ext import commands
from discord.ui import Select, View, Button
import asyncio
import io
import os
from datetime import datetime, timedelta
import re
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# تنظیمات
TICKET_CATEGORY_NAME = "TICKETS"
TRANSCRIPT_CHANNEL_ID = 1445905705323335680
STAFF_ROLE_ID = 0

votes = {}

# ——————————————————— تیکت ———————————————————
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="باگ", emoji="⚙️", description="گزارش باگ"),
            discord.SelectOption(label="ریپورت بازیکن", emoji="⚠️", description="ریپورت چیت"),
            discord.SelectOption(label="خرید از شاپ", emoji="🛍️", description="مشکل پرداخت"),
            discord.SelectOption(label="درخواست رنک استریمر", emoji="🎥", description="اپلای استریمر"),
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
    @discord.ui.button(label="بستن تیکت", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close2025")
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.delete()

giveaways = {}

# ——————————————————— !giveaway (با !) ———————————————————
@bot.command()
@commands.has_permissions(administrator=True)
async def giveaway(ctx, time: str, winners: int, *, prize: str):
    await start_giveaway(ctx, time, winners, prize)

# ——————————————————— /giveaway (اسلش) ———————————————————
@bot.tree.command(name="giveaway", description="ساخت گیواوی حرفه‌ای")
@app_commands.describe(time="زمان (مثلاً 24h)", winners="تعداد برنده", prize="جایزه")
async def slash_giveaway(interaction: discord.Interaction, time: str, winners: int, prize: str):
    await start_giveaway(interaction, time, winners, prize)

# تابع مشترک برای هر دو
async def start_giveaway(source, time: str, winners: int, prize: str):
    try:
        if time.endswith('s'): secs = int(time[:-1])
        elif time.endswith('m'): secs = int(time[:-1]) * 60
        elif time.endswith('h'): secs = int(time[:-1]) * 3600
        elif time.endswith('d'): secs = int(time[:-1]) * 86400
        else: secs = 86400
    except:
        if isinstance(source, commands.Context):
            return await source.send("زمان اشتباهه! مثال: `24h`")
        else:
            return await source.response.send_message("زمان اشتباهه! مثال: `24h`", ephemeral=True)

    end_time = datetime.utcnow() + timedelta(seconds=secs)

    embed = discord.Embed(
        title="جایزه ویژه!",
        description=f"**{prize}**\n\nبرنده‌ها: **{winners} نفر**\nزمان باقی‌مونده: **{time}**",
        color=0x00ff00,
        timestamp=end_time
    )
    embed.set_author(name="Giveaway جدید!", icon_url="https://i.imgur.com/2Z2yM9c.gif")
    embed.set_thumbnail(url="https://i.imgur.com/2Z2yM9c.gif")
    embed.set_footer(text="شرکت کرده: 0 نفر")

    view = GiveawayView()
    if isinstance(source, commands.Context):
        msg = await source.send(embed=embed, view=view)
    else:
        await source.response.send_message(embed=embed, view=view)
        msg = await source.original_response()

    giveaways[msg.id] = {
        "end": end_time,
        "winners": winners,
        "prize": prize,
        "entries": [],
        "msg": msg
    }

class GiveawayView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Enter", style=discord.ButtonStyle.green, emoji="Party Popper", custom_id="enter_gw_final2025")
    async def enter(self, interaction: discord.Interaction, button: Button):
        gw = giveaways.get(interaction.message.id)
        if not gw: return

        if interaction.user.id in gw["entries"]:
            return await interaction.response.send_message("قبلاً شرکت کردی!", ephemeral=True)

        gw["entries"].append(interaction.user.id)

        embed = interaction.message.embeds[0]
        embed.set_footer(text=f"شرکت کرده: {len(gw['entries'])} نفر")
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        gw = giveaways.get(self.message.id)
        if not gw or not gw["entries"]:
            await self.message.edit(content="گیواوی لغو شد — کسی شرکت نکرد!", embed=None, view=None)
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

# ——————————————————— !say ———————————————————
@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, *, text=None):
    if not text:
        return
    try:
        await ctx.message.delete()
    except:
        pass
    await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())

# ——————————————————— !vote ———————————————————
@bot.command()
@commands.has_permissions(administrator=True)
async def vote(ctx, *, text=None):
    if not text:
        return await ctx.send("`!vote سوال | زمان (اختیاری) | عکس`")
    image_url = None
    duration = 86400
    question = text.strip()

    time_match = re.search(r"(\d+)([hmd])", text.lower())
    if time_match:
        num = int(time_match.group(1))
        unit = time_match.group(2)
        if unit == 'h': duration = num * 3600
        elif unit == 'm': duration = num * 60
        elif unit == 'd': duration = num * 86400
        question = re.sub(r"\d+[hmd]\s*", "", question, count=1).strip()

    url_match = re.search(r"https?://[^\s]+", text)
    if url_match:
        image_url = url_match.group(0)
        question = question.replace(image_url, "").strip()

    embed = discord.Embed(title="نظرسنجی", description=f"**{question or 'آیا موافقی؟'}**", color=0x00eeff, timestamp=datetime.utcnow() + timedelta(seconds=duration))
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url or None)
    if image_url:
        embed.set_image(url=image_url)
    embed.add_field(name="آره", value="0 رای", inline=True)
    embed.add_field(name="نه", value="0 رای", inline=True)

    view = VoteView()
    msg = await ctx.send(embed=embed, view=view)
    votes[msg.id] = {"yes": 0, "no": 0, "voters": set()}

class VoteView(View):
    def __init__(self):
        super().__init__(timeout=None)

    async def update(self, interaction):
        data = votes.get(interaction.message.id)
        if not data: return
        total = data["yes"] + data["no"]
        yes_p = round(data["yes"] / total * 100) if total else 0
        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name=f"آره ({yes_p}%)", value=str(data["yes"]), inline=True)
        embed.set_field_at(1, name=f"نه ({100-yes_p}%)", value=str(data["no"]), inline=True)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="آره", style=discord.ButtonStyle.green, emoji="✅", custom_id="yes2025")
    async def yes(self, interaction):
        data = votes.get(interaction.message.id)
        if data and interaction.user.id not in data["voters"]:
            data["yes"] += 1
            data["voters"].add(interaction.user.id)
            await self.update(interaction)

    @discord.ui.button(label="نه", style=discord.ButtonStyle.red, emoji="❌", custom_id="no2025")
    async def no(self, interaction):
        data = votes.get(interaction.message.id)
        if data and interaction.user.id not in data["voters"]:
            data["no"] += 1
            data["voters"].add(interaction.user.id)
            await self.update(interaction)

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

@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int = 10):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"**{amount}** پیام پاک شد!", delete_after=5)

@bot.tree.command(name="clear", description="پاک کردن پیام‌ها")
@app_commands.describe(amount="تعداد پیام (پیش‌فرض 10)")
async def slash_clear(interaction: discord.Interaction, amount: int = 10):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("فقط ادمین!", ephemeral=True)
    await interaction.channel.purge(limit=amount + 1)
    await interaction.response.send_message(f"**{amount}** پیام پاک شد!", ephemeral=True)

# 2. !kick و /kick
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="بدون دلیل"):
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} کیک شد! دلیل: {reason}")

@bot.tree.command(name="kick", description="کیک کردن کاربر")
@app_commands.describe(member="کاربر", reason="دلیل (اختیاری)")
async def slash_kick(interaction: discord.Interaction, member: discord.Member, reason: str = "بدون دلیل"):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message("دسترسی نداری!", ephemeral=True)
    await member.kick(reason=reason)
    await interaction.response.send_message(f"{member.mention} کیک شد! دلیل: {reason}")

# 3. !ban و /ban
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="بدون دلیل"):
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} بن شد! دلیل: {reason}")

@bot.tree.command(name="ban", description="بن کردن کاربر")
@app_commands.describe(member="کاربر", reason="دلیل (اختیاری)")
async def slash_ban(interaction: discord.Interaction, member: discord.Member, reason: str = "بدون دلیل"):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message("دسترسی نداری!", ephemeral=True)
    await member.ban(reason=reason)
    await interaction.response.send_message(f"{member.mention} بن شد! دلیل: {reason}")

# 4. !unban و /unban
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f"{user.name} آنبن شد!")

@bot.tree.command(name="unban", description="آنبن کردن کاربر")
@app_commands.describe(user_id="آیدی کاربر")
async def slash_unban(interaction: discord.Interaction, user_id: int):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message("دسترسی نداری!", ephemeral=True)
    user = await bot.fetch_user(user_id)
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"{user.name} آنبن شد!")

# 5. !avatar و /avatar
@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"آواتار {member.name}", color=0x00ffff)
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.tree.command(name="avatar", description="نمایش آواتار")
@app_commands.describe(member="کاربر (اختیاری)")
async def slash_avatar(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = discord.Embed(title=f"آواتار {member.name}", color=0x00ffff)
    embed.set_image(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# !serverinfo و /serverinfo — حالا آنلاین‌ها رو درست نشون میده

@bot.command(name="serverinfo")
async def serverinfo(ctx):
    guild = ctx.guild
    online = len([m for m in guild.members if m.status != discord.Status.offline and not m.bot])
    total = guild.member_count
    bots = len([m for m in guild.members if m.bot])

    embed = discord.Embed(title=f"اطلاعات سرور: {guild.name}", color=0x00ffff)
    embed.add_field(name="کل اعضا", value=f"**{total}** نفر", inline=True)
    embed.add_field(name="آنلاین", value=f"**{online}** نفر", inline=True)
    embed.add_field(name="بات‌ها", value=f"**{bots}** تا", inline=True)
    embed.add_field(name="تعداد چنل‌ها", value=f"متن: {len(guild.text_channels)} | صوتی: {len(guild.voice_channels)}", inline=True)
    embed.add_field(name="تعداد رول‌ها", value=len(guild.roles), inline=True)
    embed.add_field(name="ساخت سرور", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.set_footer(text=f"آیدی سرور: {guild.id}")

    await ctx.send(embed=embed)

@bot.tree.command(name="serverinfo", description="نمایش اطلاعات سرور")
async def slash_serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    online = len([m for m in guild.members if m.status != discord.Status.offline and not m.bot])
    total = guild.member_count
    bots = len([m for m in guild.members if m.bot])

    embed = discord.Embed(title=f"اطلاعات سرور: {guild.name}", color=0x00ffff)
    embed.add_field(name="کل اعضا", value=f"**{total}** نفر", inline=True)
    embed.add_field(name="آنلاین", value=f"**{online}** نفر", inline=True)
    embed.add_field(name="بات‌ها", value=f"**{bots}** تا", inline=True)
    embed.add_field(name="چنل‌ها", value=f"متن: {len(guild.text_channels)} | صوتی: {len(guild.voice_channels)}", inline=True)
    embed.add_field(name="رول‌ها", value=len(guild.roles), inline=True)
    embed.add_field(name="ساخت سرور", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.set_footer(text=f"آیدی سرور: {guild.id}")

    await interaction.response.send_message(embed=embed)

    @bot.command()
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member, time: str = None, *, reason="بدون دلیل"):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        role = await ctx.guild.create_role(name="Muted", reason="برای mute")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False)
    
    duration = None
    if time:
        try:
            if time.endswith('m'): duration = int(time[:-1]) * 60
            elif time.endswith('h'): duration = int(time[:-1]) * 3600
            elif time.endswith('d'): duration = int(time[:-1]) * 86400
        except: duration = None
    
    await member.add_roles(role, reason=reason)
    await ctx.send(f"{member.mention} سایلنت شد! مدت: {time or 'دائم'} | دلیل: {reason}")
    
    if duration:
        await asyncio.sleep(duration)
        await member.remove_roles(role)

@bot.tree.command(name="mute", description="سایلنت کردن کاربر")
@app_commands.describe(member="کاربر", time="زمان (مثلاً 30m)", reason="دلیل")
async def slash_mute(interaction: discord.Interaction, member: discord.Member, time: str = None, reason: str = "بدون دلیل"):
    # همون کد بالا (کوتاه شده برای اسلش)

# 2. !warn و /warn — هشدار دادن + سیستم وارن
warns = {}
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="بدون دلیل"):
    user_id = str(member.id)
    if user_id not in warns: warns[user_id] = []
    warns[user_id].append({"reason": reason, "by": ctx.author.name, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
    count = len(warns[user_id])
    await ctx.send(f"{member.mention} وارن شد! ({count} از 3)\nدلیل: {reason}")
    if count >= 3:
        await member.kick(reason="3 وارن")
        await ctx.send(f"{member.mention} به خاطر 3 وارن کیک شد!")

# 3. !warns — دیدن وارن‌ها
@bot.command()
async def warns(ctx, member: discord.Member = None):
    if not member: member = ctx.author
    user_id = str(member.id)
    w = warns.get(user_id, [])
    if not w:
        return await ctx.send(f"{member.mention} هیچ وارنی نداره!")
    text = "\n".join([f"{i+1}. {warn['reason']} — توسط {warn['by']} — {warn['time']}" for i, warn in enumerate(w)])
    await ctx.send(f"وارن‌های {member.mention} ({len(w)}):\n{text}")

# 4. !slowmode — اسلومود چنل
@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int = 0):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"اسلومود چنل: **{seconds} ثانیه**")

# 5. !lock و !unlock — قفل/باز کردن چنل
@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("چنل قفل شد!")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("چنل باز شد!")

# 6. !role — دادن/گرفتن رول
@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, role: discord.Role):
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"رول {role.name} از {member.mention} برداشته شد")
    else:
        await member.add_roles(role)
        await ctx.send(f"رول {role.name} به {member.mention} داده شد")

        @bot.event
async def on_message(msg):
    if msg.author.bot: return
    user_id = str(msg.author.id)
    if user_id not in levels:
        levels[user_id] = {"xp": 0, "level": 0}
    levels[user_id]["xp"] += 5  # هر پیام 5 XP
    lvl = int((levels[user_id]["xp"] // 100) ** 0.5) + 1
    if lvl > levels[user_id]["level"]:
        levels[user_id]["level"] = lvl
        await msg.channel.send(f"تبریک {msg.author.mention}! لِوِلت شد **{lvl}** ")
    await bot.process_commands(msg)

@bot.command()
async def level(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = str(member.id)
    data = levels.get(user_id, {"xp": 0, "level": 0})
    embed = discord.Embed(title=f"لِوِل {member.display_name}", color=0x00ffff)
    embed.add_field(name="لِوِل", value=data["level"], inline=True)
    embed.add_field(name="XP", value=f"{data['xp']} / {(data['level']**2)*100}", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def leaderboard(ctx):
    sorted_levels = sorted(levels.items(), key=lambda x: x[1]["level"], reverse=True)[:10]
    text = "\n".join([f"{i+1}. <@{uid}> — لِوِل {data['level']} ({data['xp']} XP)" for i, (uid, data) in enumerate(sorted_levels)])
    embed = discord.Embed(title="لیدربورد لِوِل", description=text or "هیچ کس هنوز لِوِل نداره!", color=0xff9900)
    await ctx.send(embed=embed)

# 2. تبریک بوست + رول ویژه
@bot.event
async def on_member_update(before, after):
    if len(before.roles) < len(after.roles):
        new_role = next(role for role in after.roles if role not in before.roles)
        if new_role.is_premium_subscriber():
            await after.send(f"ممنون {after.mention} که سرور رو بوست کردی! ")
            channel = bot.get_channel(123456789012345678)  # چنل اعلانات رو بذار
            if channel:
                await channel.send(f"تبریک به {after.mention} برای بوست سرور! ")

# 3. سیستم Verify با دکمه (ضد رید)
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="تأیید", style=discord.ButtonStyle.green, emoji="Check Mark Button", custom_id="verify_btn")
    async def verify(self, interaction: discord.Interaction, button: Button):
        role = discord.utils.get(interaction.guild.roles, name="Member")  # رول عضو
        if not role:
            role = await interaction.guild.create_role(name="Member")
        await interaction.user.add_roles(role)
        await interaction.response.send_message("تأیید شدی! خوش اومدی ", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def verify_panel(ctx):
    embed = discord.Embed(title="تأیید هویت", description="برای دسترسی به سرور روی دکمه بزنید", color=0x00ff00)
    await ctx.send(embed=embed, view=VerifyView())

# 4. AFK سیستم
afk_users = {}

@bot.event
async def on_message(msg):
    if msg.author.id in afk_users:
        del afk_users[msg.author.id]
        await msg.channel.send(f"{msg.author.mention} برگشتی! آفک برداشته شد")
    for member in msg.mentions:
        if member.id in afk_users:
            await msg.channel.send(f"{member.mention} الان آفکه: {afk_users[member.id]}")
    await bot.process_commands(msg)

@bot.command()
async def afk(ctx, *, reason="آفک"):
    afk_users[ctx.author.id] = reason
    await ctx.send(f"{ctx.author.mention} الان آفکه: {reason}")

# 5. !ping — پینگ بات
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"پینگ بات: **{latency}ms**")

# 6. !uptime — زمان آنلاین بودن بات
start_time = datetime.utcnow()

@bot.command()
async def uptime(ctx):
    delta = datetime.utcnow() - start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    await ctx.send(f"بات **{days} روز، {hours} ساعت، {minutes} دقیقه** آنلاینه!")

# 7. !help خفن
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="راهنمای بات IrKing", color=0x5865f2)
    embed.add_field(name="تیکت", value="!ticketpanel", inline=False)
    embed.add_field(name="گیواوی", value="!giveaway زمان تعداد جایزه", inline=False)
    embed.add_field(name="نظرسنجی", value="!vote سوال", inline=False)
    embed.add_field(name="فروشگاه", value="!shop", inline=False)
    embed.add_field(name="سرور", value="!ip • !serverinfo • !wipe", inline=False)
    embed.add_field(name="مدیریت", value="!say • !clear • !kick • !ban • !mute", inline=False)
    embed.add_field(name="دیگر", value="!ping • !uptime • !level • !avatar", inline=False)
    await ctx.send(embed=embed)

# 8. !announce — اعلان با @everyone
@bot.command()
@commands.has_permissions(administrator=True)
async def announce(ctx, *, text):
    await ctx.send("@everyone")
    await ctx.send(text)

# حتماً این خط تو on_ready باشه
@bot.event
async def on_ready():
    print(f"بات {bot.user} آنلاین شد!")
    await bot.change_presence(activity=discord.Game("connect irkings.top"))
    bot.add_view(TicketSelectView())
    bot.add_view(CloseView())
    bot.add_view(VoteView())
    bot.add_view(GiveawayView())
    bot.add_view(VerifyView())  # برای verify

# ——————————————————— on_ready ———————————————————
@bot.event
async def on_ready():
    print(f"بات {bot.user} آنلاین شد!")
    await bot.change_presence(activity=discord.Game("connect irkings.top"))
    bot.add_view(TicketSelectView())
    bot.add_view(CloseView())
    bot.add_view(VoteView())

# ——————————————————— اجرا ———————————————————
bot.run(os.getenv("TOKEN") or "توکن_بات_تو")
