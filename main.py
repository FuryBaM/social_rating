import os, discord, requests, json
import discord  #модуль discord api
from discord.ext import commands  #необходимый класс для обработки команд
from keep_alive import keep_alive

cogs = ["manage"]

intents = discord.Intents.all()

def get_prefix(client, message): ##first we define get_prefix
    with open('prefixes.json', 'r') as f: ##we open and read the prefixes.json, assuming it's in the same file
        prefixes = json.load(f) #load the json as prefixes
    return prefixes[str(message.guild.id)] #recieve the prefix for the guild id given

client = commands.Bot(command_prefix=(get_prefix), intents=intents)

@client.event
async def on_ready():
	with open('prefixes.json', 'r') as file: #read the prefix.json file
		prefixes = json.load(file)
	for row in prefixes:
		for guild in client.guilds:
			if str(guild.id) not in prefixes:
				with open('prefixes.json', 'w') as file:
					json.dump(">", file, indent=2)
	await client.change_presence(activity=discord.Game(name="Default prefix >"))
	keep_alive()

@client.event
async def on_guild_join(guild): #when the bot joins the guild
    with open('prefixes.json', 'r') as f: #read the prefix.json file
        prefixes = json.load(f) #load the json file

    prefixes[str(guild.id)] = '>'#default prefix

    with open('prefixes.json', 'w') as f: #write in the prefix.json "message.guild.id": "bl!"
        json.dump(prefixes, f, indent=2) #the indent is to make everything look a bit neater

@client.event
async def on_guild_remove(guild): #when the bot is removed from the guild
    with open('prefixes.json', 'r') as f: #read the file
        prefixes = json.load(f)

    prefixes.pop(str(guild.id)) #find the guild.id that bot was removed from

    with open('prefixes.json', 'w') as f: #deletes the guild.id as well as its prefix
        json.dump(prefixes, f, indent=2)
@client.command(pass_context=True, aliases=['префикс',"преф", "pref"])
@commands.has_permissions(administrator=True) #ensure that only administrators can use this command
async def prefix(ctx, prefix=">"): #command: bl!changeprefix ...
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    prefixes[str(ctx.guild.id)] = prefix

    with open('prefixes.json', 'w') as f: #writes the new prefix into the .json
        json.dump(prefixes, f, indent=2)

    await ctx.send(f'Префикс изменен на: {prefix}') #confirms the prefix it's been changed to
#next step completely optional: changes bot nickname to also have prefix in the nickname
    name=f'{prefix}BotBot'

if __name__ == "__main__":
	for extension in cogs:
		cog = f"cogs.{extension}"
		try:
			client.load_extension(cog)
		except Exception as e:
			print(e)
req = requests.head(url="https://discord.com/api/v1")
try:
	print(f"Rate limit {int(req.headers['Retry-After'])/60} minutes left")
except:
	print("No limit")

client.run(os.getenv('TOKEN'))
