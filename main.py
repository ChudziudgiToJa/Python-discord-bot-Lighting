import discord, json, os, asyncio, random

from discord import utils
from discord.ext import commands
from discord.ext.commands import has_permissions
from datetime import datetime

with open('config.json', 'r') as f:
    data = json.load(f)
    token = data['TOKEN']
    prefix = data['PREFIX']
    aktywnosc = data['AKTYWNOSC']
    
client = commands.Bot(command_prefix=prefix, intents=discord.Intents.all())
client.remove_command("help")


# - = - = - = - = - = rangs = - = - = - = - = - =

@client.event
async def on_member_join(member):
    roles = [1073212003662962718, 1056242014406049843, 992422540515475536]
    for role_id in roles:
        role = discord.utils.get(member.guild.roles, id=role_id)
        await member.add_roles(role)

# - = - = - = - = - = client = - = - = - = - = - =

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game(("odpalam się!")))
    print(f"[!] Aktywowano bota [{client.user}]")
    await asyncio.sleep(5)
    client.loop.create_task(update_channel_member_name())
    client.loop.create_task(update_channel_guild_name())
    client.loop.create_task(update_status_name())

    client.add_view(ticket_launcher())
    client.add_view(ticket_confirm())
    client.add_view(ticket_delete())

    client.add_view(podanie_launcher())
    client.add_view(podanie_confirm())
    client.add_view(podanie_delete())

    client.add_view(kategoria_luncher())

# - = - = - = - = - = loops = - = - = - = - = - =

async def update_channel_member_name():
    while True:
        channel = client.get_channel(1058437462818570410)
        member_count = len(channel.guild.members)
        await channel.edit(name=f'Użytkownicy: {member_count}')
        await asyncio.sleep(600)

async def update_channel_guild_name():
    channel = client.get_channel(1073366116883247114)
    guild = discord.utils.get(client.guilds, name="Serwis 7Light & Gildia NWN")
    roles = [discord.utils.get(guild.roles, name=role_name) for role_name in ["Lider NWN", "VLider NWN", "Członek NWN", "Rekrut NWN"]]
    members = [member for role in roles for member in guild.members if role in member.roles]
    await channel.edit(name=f'Status gildi {len(members)}/100')
    await asyncio.sleep(600)

async def update_status_name():
    while True:
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
                           description=f"> Jeśli potrzebujesz pomocy kliknij w guzik `Stworz ticket` zostanie stworzony kanał z pomocą od administracji", color = discord.Colour.green())
    embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1033109052567339160/1033886652835303464/fire.gif')
    await ctx.send(embed = embed, view = ticket_launcher())

@ticket.error
async def my_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Nie posiadasz wystarczających uprawnień, aby użyć tej komendy.")

class ticket_launcher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout = None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 300, commands.BucketType.member)

    @discord.ui.button(label = "Stworz ticket", style = discord.ButtonStyle.green, custom_id = "ticket_button", emoji="<a:icon_modshield:1073011960603488286>")
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in [user['user_id'] for user in blacklist['blacklist']]:
            await interaction.response.send_message(f"Posiadasz *BLACKLISTE*, co to oznacza? zostałeś wykluczony z użytku 7bota", ephemeral = True)
            return
        
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
            try: channel = await interaction.guild.create_text_channel(name = f"ticket-{interaction.user.id}", overwrites = overwrites,category=ticket_category, reason = f"ticket dla {interaction.user}")
            except: return await interaction.response.send_message("Nie posiadasz permisji", ephemeral = True)
            await interaction.response.send_message(f"ticket został utworzony {channel.mention}!", ephemeral = True)
            embed = discord.Embed(title=("Strefa pomocy"),
                                   description=f"Opisz swój problem.", color = discord.Colour.green())
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
        if retry: return await interaction.response.send_message(f"Sprubój ponownie za {round(retry, 1)} sekund!", ephemeral = True)

        embed = discord.Embed(title = "Czy na pewno chcesz zamknąć to zgłoszenie", color = discord.Colour.green())
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

        try: await interaction.channel.delete()
        except: await interaction.response.send_message("Nie posiadasz permisji!", ephemeral = True)

# - = - = - = - = - = padania = - = - = - = - = - =

@client.command()
@has_permissions(administrator=True)
async def podanie(ctx):
    embed = discord.Embed(title=("Strefa pomocy"),
                           description=f"> Jeżeli interesuje cię dołączenie do gildi kliknij w guzik `Stworz podanie` a zostanie stowrzony kanał z szablonem do wypełnienia", color = discord.Colour.green())
    embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1033109052567339160/1033886652835303464/fire.gif')
    await ctx.send(embed = embed, view = ticket_launcher())

@podanie.error
async def my_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Nie posiadasz wystarczających uprawnień, aby użyć tej komendy.")

class podanie_launcher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout = None)

        self.cooldown = commands.CooldownMapping.from_cooldown(1, 300, commands.BucketType.member)

    @discord.ui.button(label = "Stworz podanie",
                        style = discord.ButtonStyle.green,
                        custom_id = "podanie_button",
                        emoji="<a:icon_modshield:1073011960603488286>")
    async def podanie(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in [user['user_id'] for user in blacklist['blacklist']]:
            await interaction.response.send_message(f"Posiadasz *BLACKLISTE*, co to oznacza? zostałeś wykluczony z użytku 7bota", ephemeral = True)
            return
        
        ticket_category = utils.get(interaction.guild.categories, name = "podania")
        if ticket_category is None:
            ticket_category = await interaction.guild.create_category("podania")
        interaction.message.author = interaction.user
        retry = self.cooldown.get_bucket(interaction.message).update_rate_limit()
        if retry: return await interaction.response.send_message(f"Sprubój ponownie za {round(retry, 1)} sekund!", ephemeral = True)
        ticket = utils.get(interaction.guild.text_channels, name = f"podanie-{interaction.user.id}")
        if ticket is not None: await interaction.response.send_message(f"Masz już otwarte podanie! {ticket.mention}!", ephemeral = True)
        else:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel = False),
                interaction.user: discord.PermissionOverwrite(view_channel = True, read_message_history = True, send_messages = True, attach_files = True, embed_links = True),
                interaction.guild.me: discord.PermissionOverwrite(view_channel = True, send_messages = True, read_message_history = True), 
            }
            try: channel = await interaction.guild.create_text_channel(name = f"podanie-{interaction.user.id}", overwrites = overwrites,category=ticket_category, reason = f"podanie dla {interaction.user}")
            except: return await interaction.response.send_message("Nie posiadasz permisji", ephemeral = True)
            await interaction.response.send_message(f"podanie zostało utworzone {channel.mention}!", ephemeral = True)
            embed = discord.Embed(title=("Strefa pomocy"),
                                   description=f"Wypełnij wzór i wyślij go na chat`cie ```Wzór Podania :\n1. nick:\n2. Wiek:\n3. Nick w Minecraft ? :\n4. Jak oceniasz swoje pvp -/10 ? :\n5. Ile czasu grasz w Minecraft ? :\n6. Premium/Nonpremium?:\n7. Ile dziennie możesz poświecić czasu na gildię ? :\n8. Umiesz ładnie budować ?:\n9. Co wprowadziłbyś do gildii ?:\n10. Posiadasz :\n-Sprawny Mikrofon\n-Mutacje\n11. Umiesz pracować w grupie ?:\n12. Na stałe czy raczej na jakiś czas ?:```", color = discord.Colour.green())
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/806244893977739324/1073020064661524551/logo_napisy.png")
            await channel.send(embed=embed, view=podanie_delete())

class podanie_delete(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout = None)

        self.cooldown = commands.CooldownMapping.from_cooldown(1, 10, commands.BucketType.member)

    @discord.ui.button(label = "Zamknij",
                        style = discord.ButtonStyle.red,
                        custom_id = "close",
                        emoji="<a:icon_delete:1073011964537753711>")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        interaction.message.author = interaction.user
        retry = self.cooldown.get_bucket(interaction.message).update_rate_limit()
        if retry: return await interaction.response.send_message(f"Sprubój ponownie za {round(retry, 1)} sekund!", ephemeral = True)
        embed = discord.Embed(title = "Czy na pewno chcesz zamknąć to podanie", color = discord.Colour.green())
        try: await interaction.response.send_message(embed=embed, view=podanie_confirm(), ephemeral = True)
        except: await interaction.response.send_message("Nie posiadasz permisji!", ephemeral = True)

class podanie_confirm(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout = None)

    @discord.ui.button(label = "zatwierdz", style = discord.ButtonStyle.red,
                        custom_id = "confirm",
                        emoji="<a:icon_delete:1073011964537753711>")
    async def confirm_button(self, interaction, button):
        try: await interaction.channel.delete()
        except: await interaction.response.send_message("Nie posiadasz permisji!", ephemeral = True)

# - = - = - = - = - = kategorie = - = - = - = - = - =

@client.command()
@has_permissions(administrator=True)
async def kategorie(ctx):
    embed = discord.Embed(title=('Kategorie serwerów'),
                           description=f"Przeczytaj <#992422566574706799> , aby wybrać kategorie na serwerze.\nJeśli przeczytałeś to wiesz jakie są zasady w gildi i discordzie.\nKliknij przycisk `Serwis 7Light` lub `Gildia NWN`, aby przejść ten etap.", color = discord.Colour.green())  
    embed.set_image(url='https://i.imgur.com/wPjXE9w.jpg')
    await ctx.send(embed = embed, view = kategoria_luncher())

@kategorie.error
async def my_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Nie posiadasz wystarczających uprawnień, aby użyć tej komendy.")

class kategoria_luncher(discord.ui.View):
  def __init__(self) -> None:
    super().__init__(timeout = None)
    self.cooldown = commands.CooldownMapping.from_cooldown(1, 10, commands.BucketType.member)


  @discord.ui.button(label = "Serwis 7Light",
                    custom_id = "button_role1",
                    emoji="<a:barrier_block:1073011973639385098>",
                    style = discord.ButtonStyle.green)
  async def button_role1(self, interaction: discord.Interaction, button: discord.ui.Button):

    interaction.message.author = interaction.user
    retry = self.cooldown.get_bucket(interaction.message).update_rate_limit()
    if retry: return await interaction.response.send_message(f"Sprubój ponownie za {round(retry, 1)} sekund!", ephemeral = True)

    role1 = 999421620894568498
    user = interaction.user
    if role1 in [y.id for y in user.roles]:
      await user.remove_roles(user.guild.get_role(role1))

      await interaction.response.send_message("Usunięto kategorie (7Light)", ephemeral = True)
    else:
      await user.add_roles(user.guild.get_role(role1))
      await interaction.response.send_message("Nadano kategorie (7Light)", ephemeral = True)
  @discord.ui.button(label = "Gildia NWN",
                    custom_id = "button_role2",
                    emoji="<a:diamond_sword:1073011971043115068>",
                    style = discord.ButtonStyle.blurple)
  async def button_role2(self, interaction: discord.Interaction, button: discord.ui.Button):

    interaction.message.author = interaction.user
    retry = self.cooldown.get_bucket(interaction.message).update_rate_limit()
    if retry: return await interaction.response.send_message(f"Sprubój ponownie za {round(retry, 1)} sekund!", ephemeral = True)

    role2 = 1073212315987611658
    user = interaction.user
    if role2 in [y.id for y in user.roles]:
      await user.remove_roles(user.guild.get_role(role2))

      await interaction.response.send_message("Usunięto kategorie (Gildia NWN)", ephemeral = True)
    else:
      await user.add_roles(user.guild.get_role(role2))
      await interaction.response.send_message("Nadano kategorie (Gildia NWN)", ephemeral = True)

# - = - = - = - = - = lvl = - = - = - = - = - =

with open("users.json", "ab+") as ab:
    ab.close()
    f = open('users.json','r+')
    f.readline()
    if os.stat("users.json").st_size == 0:
      f.write("{}")
      f.close()
    else:
      pass
with open('users.json', 'r') as f:
  users = json.load(f)

@client.event    
async def on_message(message):
    if message.author.bot == False:
        with open('users.json', 'r') as f:
            users = json.load(f)
        await add_experience(users, message.author)
        await level_up(users, message.author, message)
        with open('users.json', 'w') as f:
            json.dump(users, f)
            await client.process_commands(message)

async def add_experience(users, user):
  if not f'{user.id}' in users:
        users[f'{user.id}'] = {}
        users[f'{user.id}']['experience'] = 0
        users[f'{user.id}']['level'] = 1
  users[f'{user.id}']['experience'] += 6

async def level_up(users, user, message):
  experience = users[f'{user.id}']["experience"]
  lvl_start = users[f'{user.id}']["level"]
  lvl_end = int(experience ** (1 / 5))
  if lvl_start < lvl_end:
    em1 = discord.Embed(
        title="Strefa użytkownika <:icon_beta:1073011966571970641>",
        description=f"Gratulacje zdobyłeś nowy poziom:\n\n> `Nick:`  {user.mention}\n> `Poziom:`  __*{lvl_start}*__  ->  __*{lvl_end}*__   `Doświadczenie:` {experience}",
        colour=discord.Colour.green()
        )
    em1.set_thumbnail(url='https://cdn.discordapp.com/attachments/1033109052567339160/1033886652835303464/fire.gif')

    role = discord.utils.get(message.guild.roles, name="poziom " + str(lvl_end))
    await message.author.add_roles(role)
    if role is None:
        await user.add_roles(role)

    channel= client.get_channel(1077550850421047386)
    await channel.send(embed=em1)
    users[f'{user.id}']["level"] = lvl_end
    
# - = - = - = - = - = log = - = - = - = - = - =

@client.event
async def on_message_delete(message):
    if message.author.bot == False:
        embed = discord.Embed(title="Delete",
                            description=f"`Nick:` {message.author.mention}",
                            color=0xFF0000)
        embed.add_field(name="```" + message.content + "```", value=":x:",inline=True)

        channel = client.get_channel(1079159997444935760)
        await channel.send(embed=embed)

@client.event
async def on_message_edit(message_before, message_after):
    if message_before.author.bot == False:

        embed = discord.Embed(title="Edited",
                          description=f"`Nick:` {message_before.author.mention}",
                          colour=discord.Colour.red())  
        embed.add_field(name="```" + message_before.content + "```", value=":x:",inline=True)
        embed.add_field(name="```" + message_after.content + "```", value=":white_check_mark:",inline=True)

        channel = client.get_channel(1079159997444935760)
        await channel.send(embed=embed)

# - = - = - = - = - = blacklist = - = - = - = - = - =

with open('blacklist.json') as f:
    blacklist = json.load(f)

@client.event
async def on_message(message):
    if message.author.id in [user['user_id'] for user in blacklist['blacklist']]:
        return
    else:
        await client.process_commands(message)

@client.command()
@has_permissions(administrator=True)
async def b_add(ctx, user_id: int, powód: str):
    for user in blacklist['blacklist']:
        if user['user_id'] == user_id:
            await ctx.send(f'Użytkownik o ID {user_id} już istnieje na czarnej liście.')
            return
    if user_id == 441492546028306436:
        await ctx.send(f'Użytkownik o ID {user_id} jest niemożłiwy do dodania.')
        return
    blacklist['blacklist'].append({'user_id': user_id, 'reason': powód})
    with open('blacklist.json', 'w') as f:
        json.dump(blacklist, f, indent=4)
    await ctx.send(f'Użytkownik o ID {user_id} został dodany do czarnej listy.')
    channel = client.get_channel(1081320004814901288)
    embed = discord.Embed(title="BLACKLIST",
        description=f"Dodano do listy `{user_id}`\npowód: `{powód}`",
        colour=discord.Colour.red())
    await channel.send(embed=embed)

@client.command()
@has_permissions(administrator=True)
async def b_remove(ctx, user_id: int):
    for i, user in enumerate(blacklist['blacklist']):
        if user['user_id'] == user_id:
            blacklist['blacklist'].pop(i)
            with open('blacklist.json', 'w') as f:
                json.dump(blacklist, f, indent=4)
            await ctx.send(f'Użytkownik o ID {user_id} został usunięty z czarnej listy.')
            channel = client.get_channel(1081320004814901288)
            embed = discord.Embed(title="BLACKLIST",
            description=f"Usunięto `{user_id}` z listy",
            colour=discord.Colour.red()
                )
            await channel.send(embed=embed)
            return
    await ctx.send('Nie znaleziono użytkownika na czarnej liście.')

client.run(token)