# main.py
import discord
from discord.ext import commands, tasks
from discord.ui import Select, View
from datetime import datetime, timedelta
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ==================== تنظیمات سیستم تیکت ====================
TICKET_CATEGORY_NAME = "TICKETS"
LOG_CHANNEL_ID = 1445885343948607558
TRANSCRIPT_CHANNEL_ID = 1445885343948607558
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
        await interaction.response.send_message(f"شما {choice} را انتخاب کردید!", ephemeral=True)

    select.callback = callback
    view = View(timeout=None)
    view.add_item(select)
    embed = discord.Embed(title="فروشگاه رنک IRking 10X", description="رنک مورد نظرت رو انتخاب کن:", color=0xff9900)
    await ctx.send(embed=embed, view=view)

# ==================== Ready Event ====================
@bot.event
async def on_ready():
    print(f"بات {bot.user} آماده شد!")
    bot.add_view(TicketSelectView())
    bot.add_view(TicketControlView())

# ==================== Run ====================
bot.run(os.getenv("TOKEN"))
