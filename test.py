
import discord
from discord import app_commands, utils
from discord.ext import commands
from discord.ext.commands import has_permissions
import json

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())


# - = - = - = - = - = TICKETS = - = - = - = - = - =

class ticket_launcher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout = None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 600, commands.BucketType.member)

    @discord.ui.button(label = "Stworz ticket", style = discord.ButtonStyle.green, custom_id = "ticket_button", emoji="<a:icon_modshield:1073011960603488286>")
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket_category = utils.get(interaction.guild.categories, name = "ticket")
        if ticket_category is None:
            ticket_category = await interaction.guild.create_category("ticket")

        interaction.message.author = interaction.user
        retry = self.cooldown.get_bucket(interaction.message).update_rate_limit()
        if retry: return await interaction.response.send_message(f"Sprubój ponownie za {round(retry, 1)} sekund!", ephemeral = True)
        ticket = utils.get(interaction.guild.text_channels, name = f"ticket-{interaction.user.id}")
        if ticket is not None: await interaction.response.send_message(f"Masz już otwarty ticket! {ticket.mention}!", ephemeral = True)
        else:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel = False),
                interaction.user: discord.PermissionOverwrite(view_channel = True, read_message_history = True, send_messages = True, attach_files = True, embed_links = True),
                interaction.guild.me: discord.PermissionOverwrite(view_channel = True, send_messages = True, read_message_history = True), 
            }
            try: channel = await interaction.guild.create_text_channel(name = f"ticket-{interaction.user.id}", overwrites = overwrites, reason = f"ticket dla {interaction.user}")
            except: return await interaction.response.send_message("Nie posiadasz permisji", ephemeral = True)
            await interaction.response.send_message(f"ticket został utworzony {channel.mention}!", ephemeral = True)
            embed = discord.Embed(title=("Strefa pomocy"), description=f"Opisz swój problem.\n\n> !ticket_close -zamyka kanał.", colour= 0x5EFF0E,)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/806244893977739324/1073020064661524551/logo_napisy.png")
            await channel.send(embed=embed, view = close())

@client.command()
async def ticket(ctx):
    embed = discord.Embed(title=("Strefa pomocy"), description=f"> Jeśli potrzebujesz pomocy kliknij w guzik `Stworz ticket` zostanie stworzony kanał z pomocą od administracji\n\n> Pingowanie administracji jest surowo `karane`\n> Limit ticketów `1`",colour= 0x5EFF0E,)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/806244893977739324/1073020064661524551/logo_napisy.png")
    await ctx.send(embed = embed, view = ticket_launcher())


class close(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout = None)
    
    @discord.ui.button(label = "Zamknij ticket 2", style = discord.ButtonStyle.red, custom_id = "close", emoji="<:icon_modshield:1073011960603488286>")
    async def close(self, interaction, button):
        embed = discord.Embed(title = "Czy na pewno chcesz zamknąć to zgłoszenie", color = discord.Colour.blurple())
        await interaction.response.send_message(embed = embed, ephemeral = True)

# - = - = - = - = - = LOGS = - = - = - = - = - =



client.run("MTAzNjQwNTAxMzM2NDM0NzAzMg.GHeLk4.hbk1uddyekUAu0kBwmI-uH771bXOci8U7PIwJ8")