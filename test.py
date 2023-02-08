
import discord
from discord import app_commands, utils
from discord.ext import commands
import json

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())


# - = - = - = - = - = TICKETS = - = - = - = - = - =

class ticket_launcher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout = None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 5, commands.BucketType.member)
    
    @discord.ui.button(label = "Stworz ticket", style = discord.ButtonStyle.green, custom_id = "ticket_button")
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
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
            try: channel = await interaction.guild.create_text_channel(name = f"ticket-{interaction.user.id}", overwrites = overwrites, reason = f"Ticket for {interaction.user.discriminator}")
            except: return await interaction.response.send_message("Sprawdz czy posiadasz permisje", ephemeral = True)
            await interaction.response.send_message(f"ticket został utworzony {channel.mention}!", ephemeral = True)


@client.command()
async def ticket(ctx):
    embed = discord.Embed(title=(":ticket:Strefa pomocy"), description=f"wew", colour= 0xff6600,)  
    await ctx.send(embed = embed, view = ticket_launcher())

@client.command()
async def delete(ctx):
    await ctx.channel.delete()

client.run("MTAzNjQwNTAxMzM2NDM0NzAzMg.GHeLk4.hbk1uddyekUAu0kBwmI-uH771bXOci8U7PIwJ8")