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

# ——————————————————— دستور !say (هر چی بنویسی می‌فرسته) ———————————————————
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

# ——————————————————— دستور !vote (مثل ProBot) ———————————————————
@bot.command()
@commands.has_permissions(administrator=True)
async def vote(ctx, *, text=None):
    if not text:
        return await ctx.send("`!vote سوال (اختیاری: زمان و عکس)`")

    image_url = None
    duration = 86400
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

    # تشخیص عکس
    url_match = re.search(r"(https?://\S+\.(?:png|jpg|jpeg|gif|webp))", text)
    if url_match:
        image_url = url_match.group(1)
        question = question.replace(url_match.group(1), "").strip()

    embed = discord.Embed(title="نظرسنجی", description=f"**{question or 'رای بدهید!'}**", color=0x5865f2)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url or None)
    if image_url:
        embed.set_image(url=image_url)
    embed.add_field(name="آره", value="0 رای", inline=True)
    embed.add_field(name="نه", value="0 رای", inline=True)
    embed.set_footer(text="پایان نظرسنجی")

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
        yes_p = int(data["yes"] / total * 100) if total > 0 else 0
        no_p = 100 - yes_p
        bar = "Green Square" * int(yes_p / 10) + "White Square" * (10 - int(yes_p / 10))

        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name=f"آره ({yes_p}%)", value=f"{bar} {data['yes']} رای", inline=True)
        embed.set_field_at(1, name=f"نه ({no_p}%)", value=f"{bar[::-1] if no_p > yes_p else 'White Square'*10} {data['no']} رای", inline=True)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="آره", style=discord.ButtonStyle.green, emoji="Check Mark Button", custom_id="vote_yes")
    async def yes(self, interaction):
        data = votes.get(interaction.message.id)
        if not data or interaction.user.id in data["voters"]:
            return await interaction.response.send_message("قبلاً رای دادی!", ephemeral=True)
        data["yes"] += 1
        data["voters"].add(interaction.user.id)
        await self.update(interaction)

    @discord.ui.button(label="نه", style=discord.ButtonStyle.red, emoji="Cross Mark", custom_id="vote_no")
    async def no(self, interaction):
        data = votes.get(interaction.message.id)
        if not data or interaction.user.id in data["voters"]:
            return await interaction.response.send_message("قبلاً رای دادی!", ephemeral=True)
        data["no"] += 1
        data["voters"].add(interaction.user.id)
        await self.update(interaction)

# ——————————————————— دستورات دیگر ———————————————————
@bot.command()
async def ip(ctx):
    await ctx.send(embed=discord.Embed(title="آدرس سرور", description="```connect irkings.top```", color=0xff9900))

@bot.command()
async def cart(ctx):
    embed = discord.Embed(title="کارت به کارت", color=0xff9900)
    embed.add_field(name="شماره کارت", value="```6219-8618-1827-9068```", inline=False)
    embed.add_field(name="به نام", value="**فرهاد حسینی**", inline=False)
    await ctx.send(embed=embed)

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
