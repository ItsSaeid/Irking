import discord
from discord.ext import commands
from discord.ui import Select, View

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"بات {bot.user} با موفقیت روشن شد! IRking 10X 24/7")


@bot.command()
async def shop(ctx):
    select = Select(placeholder="رنک مورد نظرت رو انتخاب کن...",
                    options=[
                        discord.SelectOption(
                            label="Legendary",
                            value="legendary",
                            emoji="🏅",
                            description="ماه | هفته | 360 تومان | 84 تومان"),
                        discord.SelectOption(
                            label="Elite Commander",
                            value="elite",
                            emoji="💠",
                            description="ماه | هفته | 480 تومان | 112 تومان"),
                        discord.SelectOption(
                            label="GameMaster",
                            value="gamemaster",
                            emoji="👑",
                            description="ماه | هفته | 640 تومان | 149 تومان"),
                        discord.SelectOption(
                            label="Overlord",
                            value="overlord",
                            emoji="💎",
                            description="ماه | هفته | 800 تومان | 184 تومان"),
                    ])

    async def callback(interaction):
        choice = interaction.data['values'][0]

        ranks = {
            "legendary": {
                "title":
                "رنک Legendary",
                "color":
                0x00ff00,
                "price30":
                "360,000 تومان",
                "price7":
                "84,000 تومان",
                "perks":
                "• روشن کردن تورت\n• کیت مخصوص\n• افزایش سرعت آپگرید\n• mymini / myheli / myattack بدون کولداون\n• no cold & hot\n• reward بیشتر\n• بک‌پک بزرگتر\n• سرعت تله‌پورت بیشتر\n• سثوم بیشتر",
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
                "title":
                "رنک Elite Commander",
                "color":
                0x00ffff,
                "price30":
                "480,000 تومان",
                "price7":
                "112,000 تومان",
                "perks":
                "• همه مزایای Legendary\n• کیت قوی‌تر\n• /back و /craft\n• هلیکوپتر شخصی\n• برداشت سنگ پخته\n• افزایش سرعت تله‌پورت",
                "images": [
                    "https://uploadkon.ir/uploads/b20714_25Rust-11-14-2025-5-26-05-PM.png",
                    "https://uploadkon.ir/uploads/a4c214_25Rust-11-14-2025-5-26-11-PM.png",
                    "https://uploadkon.ir/uploads/b67f14_25Rust-11-14-2025-5-26-15-PM.png",
                    "https://uploadkon.ir/uploads/b41614_25Rust-11-14-2025-5-26-20-PM.png",
                    "https://uploadkon.ir/uploads/d98014_25Rust-11-14-2025-5-26-25-PM.png"
                ]
            },
            "gamemaster": {
                "title":
                "رنک GameMaster",
                "color":
                0xffff00,
                "price30":
                "640,000 تومان",
                "price7":
                "149,000 تومان",
                "perks":
                "• همه مزایای Elite\n• بدون کولداون کیت\n• No Radiation & No Bleeding\n• هلیکوپتر و مینی دائمی\n• دسترسی نیمه ادمین",
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
                "title":
                "رنک Overlord",
                "color":
                0xff00ff,
                "price30":
                "800,000 تومان",
                "price7":
                "186,000 تومان",
                "perks":
                "• همه چیز + نقش اختصاصی\n• تبلیغ دائمی سرور\n• دسترسی کامل ادمین\n• اولویت در همه چیز\n• کیت اختصاصی دائمی",
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

        # اولین پیام با اطلاعات کامل
        embed = discord.Embed(title=data["title"], color=data["color"])
        embed.add_field(name="قیمت ۳۰ روز", value=data["price30"], inline=True)
        embed.add_field(name="قیمت ۷ روز", value=data["price7"], inline=True)
        embed.add_field(name="مزایا", value=data["perks"], inline=False)
        embed.set_image(url=data["images"][0])
        embed.set_footer(
            text=f"عکس ۱ از {len(data['images'])} | برای خرید تیکت بزن")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # بقیه عکس‌ها یکی‌یکی
        for i in range(1, len(data["images"])):
            emb = discord.Embed(color=data["color"])
            emb.set_image(url=data["images"][i])
            emb.set_footer(
                text=f"عکس {i+1} از {len(data['images'])} | برای خرید تیکت بزن"
            )
            await interaction.followup.send(embed=emb, ephemeral=True)

    select.callback = callback
    view = View(timeout=None)
    view.add_item(select)

    main_embed = discord.Embed(title="فروشگاه رنک IRking 10X",
                               description="رنک مورد نظرت رو انتخاب کن:",
                               color=0xff9900)
    main_embed.set_thumbnail(
        url=
        "https://uploadkon.ir/uploads/f8c114_256b0e13495ed97b05b29e3481ef68f708.png"
    )  # بنرت رو عوض کن
    await ctx.send(embed=main_embed, view=view)


bot.run(os.getenv("TOKEN"))
