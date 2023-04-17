import discord, json, os, asyncio, random, traceback, openai, math

from discord import utils
from discord.ext import commands
from discord.ext.commands import has_permissions
from datetime import datetime

with open('config.json', 'r') as f:
    data = json.load(f)
    token = data['TOKEN']
    prefix = data['PREFIX']
    aktywnosc = data['AKTYWNOSC']
    owner_id = data['OWNER_ID']
    
client = commands.Bot(command_prefix=prefix, intents=discord.Intents.all(), help_command=None)

# - = - = - = - = - = rangs = - = - = - = - = - =

@client.event
async def on_member_join(member):
    roles = [1073212003662962718, 1056242014406049843, 992422540515475536]
    for role_id in roles:
        role = discord.utils.get(member.guild.roles, id=role_id)
        await member.add_roles(role)

# - = - = - = - = - = client = - = - = - = - = - =

@client.event
async def on_error(event, *args, **kwargs):
    error_message = traceback.format_exc()
    user = await client.fetch_user(owner_id)
    await user.send(f"**Wystąpił błąd:**\n```\n{error_message}\n```")

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game(("odpalam się!")))
    print(f"[!] Aktywowano bota [{client.user}]")
    client.loop.create_task(loop_ten_min())

    client.add_view(ticket_launcher())
    client.add_view(ticket_confirm())
    client.add_view(ticket_delete())
    
# - = - = - = - = - = loops = - = - = - = - = - =

async def loop_ten_min():
    while True:
        channel = client.get_channel(1096943790926868521)
        member_count = len(channel.guild.members)
        await channel.edit(name=f'ᴜᴢʏᴛᴋᴏᴡɴɪᴄʏ: {member_count}')
        await client.change_presence(status=discord.Status.online, activity=discord.Game(random.choice(aktywnosc)))
        await asyncio.sleep(600)

@client.event 
async def on_command_error(ctx, error): 
    if isinstance(error, commands.CommandNotFound): 
        return

# - = - = - = - = - = tickety = - = - = - = - = - =

@client.command()
@has_permissions(administrator=True)
async def ticket(ctx):
    embed = discord.Embed(title=("Strefa pomocy"),
                           description=f"> Jeśli potrzebujesz pomocy kliknij w guzik `Stworz ticket` zostanie stworzony kanał z pomocą od administracji", color = discord.Colour.orange())
    embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1033109052567339160/1033886652835303464/fire.gif')
    await ctx.send(embed = embed, view = ticket_launcher())

@ticket.error
async def my_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Nie posiadasz wystarczających uprawnień, aby użyć tej komendy.")

class ticket_launcher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout = None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.member)

    @discord.ui.button(label = "Stworz ticket", style = discord.ButtonStyle.green, custom_id = "ticket_button", emoji="<a:icon_modshield:1073011960603488286>")
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ticket_create())

class ticket_create(discord.ui.Modal, title='formularz rekrutacyjny'):
    pytanie_1 = discord.ui.TextInput(label='Opisz swój problem / pytanie.',style=discord.TextStyle.paragraph ,max_length=500)
    async def on_submit(self, interaction: discord.Interaction):
        ticket_category = utils.get(interaction.guild.categories, name = "ticket")
        if ticket_category is None:
            ticket_category = await interaction.guild.create_category("ticket")
        interaction.message.author = interaction.user
        ticket = utils.get(interaction.guild.text_channels, name = f"ticket-{interaction.user.id}")
        if ticket is not None: await interaction.response.send_message(f"Masz już otwarty ticket! {ticket.mention}!", ephemeral = True)
        else:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel = False),
                interaction.user: discord.PermissionOverwrite(view_channel = True, read_message_history = True, send_messages = True, attach_files = True, embed_links = True),
                interaction.guild.me: discord.PermissionOverwrite(view_channel = True, send_messages = True, read_message_history = True), 
            }
            try: channel = await interaction.guild.create_text_channel(name = f"ticket-{interaction.user.id}", overwrites = overwrites,category=ticket_category, reason = f"ticket dla {interaction.user}")
            except: return await interaction.response.send_message("Nie posiadasz permisji", ephemeral = True)
            await interaction.response.send_message(f"ticket został utworzony {channel.mention}!", ephemeral = True)
            log = 1096967443571810346
            channel_log = client.get_channel(log)
            await channel_log.send(f"{interaction.user} utworzył ticket")
            embed = discord.Embed(title=("Strefa pomocy"),
                                   description=f"Pytanie od: `{interaction.user}` \n\n > {self.pytanie_1.value}", color = discord.Colour.green())
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/806244893977739324/1073020064661524551/logo_napisy.png")
            await channel.send(embed=embed, view=ticket_delete())

class ticket_delete(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout = None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 10, commands.BucketType.member)

    @discord.ui.button(label = "Zamknij", style = discord.ButtonStyle.red, custom_id = "close", emoji="<a:icon_delete:1073011964537753711>")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        interaction.message.author = interaction.user
        retry = self.cooldown.get_bucket(interaction.message).update_rate_limit()
        if retry: return await interaction.response.send_message(f"Spróbuj ponownie za {round(retry, 1)} sekund!", ephemeral = True)

        embed = discord.Embed(title = "Czy na pewno chcesz zamknąć to zgłoszenie", color = discord.Colour.orange())
        try: await interaction.response.send_message(embed=embed, view=ticket_confirm(), ephemeral = True)
        except: await interaction.response.send_message("Nie posiadasz permisji!", ephemeral = True)

class ticket_confirm(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout = None)

    @discord.ui.button(label = "zatwierdz",
                        style = discord.ButtonStyle.red,
                        custom_id = "confirm",
                        emoji="<a:icon_delete:1073011964537753711>")
    async def confirm_button(self, interaction, button):
        user = interaction.user
        if user.guild_permissions.administrator:
            await interaction.channel.delete()
            log = 1096967443571810346
            channel_log = client.get_channel(log)
            await channel_log.send(f"{interaction.user} zamyka ticket")
        else:
            await interaction.response.send_message("Nie posiadasz permisji!", ephemeral=True)
            return

# - = - = - = - = - = kategorie = - = - = - = - = - =

@client.command()
@has_permissions(administrator=True)
async def startup(ctx):
    embed = discord.Embed(title=('Kategorie'),
                           description=f"Przeczytaj <#992422566574706799> , aby wybrać kategorie na serwerze.\nJeśli przeczytałeś to wiesz jakie są zasady na discordzie.\nKliknij przycisk aby przejść ten etap.", color = discord.Colour.dark_orange())  
    await ctx.send(embed = embed, view = startup_luncher())

@startup.error
async def my_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Nie posiadasz wystarczających uprawnień, aby użyć tej komendy.")

class startup_luncher(discord.ui.View):
  def __init__(self) -> None:
    super().__init__(timeout = None)
    self.cooldown = commands.CooldownMapping.from_cooldown(1, 10, commands.BucketType.member)
  @discord.ui.button(label = "Akceptuje regulamin",
                    custom_id = "button_role1",
                    emoji="<a:icon_join:1073011962092458104>",
                    style = discord.ButtonStyle.green
                    )
  async def button_role1(self, interaction: discord.Interaction, button: discord.ui.Button):
        interaction.message.author = interaction.user
        retry = self.cooldown.get_bucket(interaction.message).update_rate_limit()
        if retry: return await interaction.response.send_message(f"Spróbuj ponownie za {round(retry, 1)} sekund!", ephemeral = True)
        log = 1093666927873892422
        role = 1093662561049784420
        user = interaction.user
        channel_log = client.get_channel(log)
        if role in [y.id for y in user.roles]:
            await user.remove_roles(user.guild.get_role(role))
            await interaction.response.send_message("Usunięto role (7Light)", ephemeral = True)
            await channel_log.send(f"{interaction.user.display_name} Usunięto role (7Light)")
        else:
            await user.add_roles(user.guild.get_role(role))
            await interaction.response.send_message("Nadano role (Gildia NWN)", ephemeral = True)
            await channel_log.send(f"{interaction.user.display_name} Nadano role (7Light)")

# - = - = - = - = - = log = - = - = - = - = - =

@client.event
async def on_message_delete(message):
    if message.author.bot == False:
        embed = discord.Embed(title="Delete",
                            description=f"`Nick:` {message.author.mention}",
                            color=0xFF0000)
        embed.add_field(name="```" + message.content + "```", value=":x:",inline=True)
        
        for attachment in message.attachments:
            embed.set_image(url=attachment.url)

        channel = client.get_channel(1096934505165635705)
        await channel.send(embed=embed)

@client.event
async def on_message_edit(message_before, message_after):
    if message_before.author.bot == False:

        embed = discord.Embed(title="Edited",
                          description=f"`Nick:` {message_before.author.mention}",
                          colour=discord.Colour.red())  
        embed.add_field(name="```" + message_before.content + "```", value=":x:",inline=True)
        embed.add_field(name="```" + message_after.content + "```", value=":white_check_mark:",inline=True)

        # pętla dla załączników
        for attachment in message_before.attachments + message_after.attachments:
            embed.set_image(url=attachment.url)

        channel = client.get_channel(1096934505165635705)
        await channel.send(embed=embed)

client.run(token)