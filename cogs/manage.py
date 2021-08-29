import os, discord, random, sqlite3, json, aiocron, glob
import numpy as np
from datetime import datetime
from discord.ext import commands 
from operator import itemgetter
conn=sqlite3.connect("database.db", check_same_thread=False)
cursor=conn.cursor()
rates=["неудовлетворительно", "почти удовлетворительно", "удовлетворительно", "весьма удовлетворительно", "почти хорошо", "хорошо", "очень хорошо", "почти отлично", "отлично", "превосходно"]
maxRate=3000
positives=["Партия гордится тобой!", "Партия гордость тебе!", "Партия гордится тобой - ты быть настоящий герой человек!", "Группировка Цисин гордится тобой!!!", "Партия гордится Вами!", "Партия гордится ты!", "Партия довольна тобой!"]
negatives=["Ну и ну! Вы разочаровываете партию.", "Ужас! Ехать санаторий отдых Уйгнур!", "Думать перед писать следующий раз!", "Тайванец обнаружен!. Кукарекай в другом месте!", "Вы делать Китай партия плохо", "Умри грязь уйгур", "Партия и Великий товарищ Xi разочарованы тобой!", "Вы оклеветали Китай!", "Партия разочарована!"]
class Manager(commands.Cog):
	def __init__(self, client):
		self.client=client
		@aiocron.crontab('0 0 * * *')
		async def cronjob1():
			cursor.execute(f"UPDATE members SET actions=5")
			conn.commit()
			print("Actions reseted")
			user=self.client.get_user(425141159510278144)
			await user.send(f"Updated at {datetime.now()}")
	@commands.Cog.listener()
	async def on_ready(self):
		cursor.execute(f"SELECT * FROM members")
		result = cursor.fetchall()
		guilds = list(set(result))
		for guild in self.client.guilds:
			try:
				role = discord.utils.get(guild.roles, name="Нарушитель")
				if role is None:
					role = await guild.create_role(name="Нарушитель")
			except Exception as err:
				print(f"Forbidden to create role in {guild.name}\n{err}")
			cursor.execute(f"SELECT * FROM members where guildID={guild.id}")
			result = cursor.fetchall()
			for member in guild.members:
				output = [item for item in guilds if item[1] == member.id and item[0] == guild.id]
				if len(output)<=0:
					if not member.bot:
						cursor.execute(f"INSERT INTO members VALUES ({guild.id}, '{member.id}', 1500, 5)")
		for guild in guilds:
			if self.client.get_guild(guild[0]) not in self.client.guilds:
				cursor.execute(f"DELETE FROM members where guildID = {guild[0]}")
		conn.commit()

	@commands.Cog.listener()
	async def on_message(self, message):
		if self.client.user.mention in message.content:
			with open('prefixes.json', 'r') as f: 
				prefixes = json.load(f) #load the json as prefixes
			await message.channel.send(f"Мой префикс: {prefixes[str(message.guild.id)]}")
	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		for member in guild.members:
			if not member.bot:
				cursor.execute(f"INSERT INTO members VALUES ({guild.id}, '{member.id}', 1500, 5)")
		conn.commit()
	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		cursor.execute(f"SELECT * FROM members where guildID={guild.id}")
		result=cursor.fetchall()
		for server in result:
			cursor.execute(f"DELETE FROM members where guildID={guild.id}")
			conn.commit()
	
	@commands.Cog.listener()
	async def on_member_join(self, member):
		if not member.bot:
			cursor.execute(f"INSERT INTO members VALUES ({member.guild.id}, '{member.id}', 1500, 5)")
			conn.commit()

	@commands.command(help="Изменить у участника баллы", brief="Изменить баллы")
	@commands.has_permissions(administrator=True)
	async def set(self, ctx, member:discord.Member=None, rating: int=1500):
		if member is None:
			member=ctx.author
		if not member.bot:
			if rating<0:
				rating = 0
			elif rating>maxRate:
				rating = maxRate
			embed=discord.Embed(title="Изменение", description=f"Балл участника {member} изменен на `{rating}`", color=0xFFFF00)
			await ctx.send(embed=embed)	
			cursor.execute(f"UPDATE members SET rating = {rating} where guildID = {ctx.guild.id} and memberID = {member.id}")
			conn.commit()
			role = discord.utils.get(ctx.guild.roles, name="Нарушитель")
			if role is None:
				role = await ctx.guild.create_role(name="Нарушитель")
			if rating<1000:
				while role not in member.roles:
					await member.add_roles(role)
				print("add")
			else:
				while role in member.roles:
					await member.remove_roles(role)
				print("remove")

	@commands.command(help="Добавить баллы", brief="Добавить баллы" )
	@commands.has_permissions(administrator=True)
	async def add(self, ctx, member:discord.Member=None, rating:int=0):
		if member is None:
			member=ctx.author
		if not member.bot:
			dbrating = 0
			cursor.execute(f"SELECT * FROM members where guildID={ctx.guild.id} and memberID={member.id}")
			result=cursor.fetchall()
			for row in result:
				dbrating = row[2]
			if rating<0:
				rating = 0
			elif rating>maxRate:
				rating = maxRate
			rate = dbrating+rating
			if rate<0:
				rate = 0
			elif rate>maxRate:
				rate = maxRate
			cursor.execute(f"UPDATE members SET rating = {rate} where guildID = {ctx.guild.id} and memberID = {member.id}")
			conn.commit()
			embed=discord.Embed(title=random.choice(positives), description=f"Рейтинг участника {member} повысился на `{rating}` баллов. Теперь у него `{rate}` баллов", color=0x00FF00)
			await ctx.send(embed=embed)
			role = discord.utils.get(ctx.guild.roles, name="Нарушитель")
			if role is None:
				role = await ctx.guild.create_role(name="Нарушитель")
			if rate<1000:
				await member.add_roles(role)
			else:
				await member.remove_roles(role)

	@commands.command(help="Отобрать баллы", brief="Отобрать баллы", aliases=['rm'])
	@commands.has_permissions(administrator=True)
	async def remove(self, ctx, member:discord.Member=None, rating:int=0):
		if member is None:
			member=ctx.author
		if not member.bot:
			dbrating = 0
			cursor.execute(f"SELECT * FROM members where guildID={ctx.guild.id} and memberID={member.id}")
			result=cursor.fetchall()
			for row in result:
				dbrating = row[2]
			if rating<0:
				rating = 0
			elif rating>maxRate:
				rating = maxRate
			rate = dbrating-rating
			if rate<0:
				rate = 0
			elif rate>maxRate:
				rate = maxRate
			cursor.execute(f"UPDATE members SET rating = {rate} where guildID = {ctx.guild.id} and memberID = {member.id}")
			conn.commit()
			embed=discord.Embed(title=random.choice(negatives), description=f"Рейтинг участника {member} уменьшился на `{rating}` баллов. Теперь у него `{rate}` баллов.", color=0xFF0000)
			await ctx.send(embed=embed)
			role = discord.utils.get(ctx.guild.roles, name="Нарушитель")
			if role is None:
				role = await ctx.guild.create_role(name="Нарушитель")
			if rate<1000:
				await member.add_roles(role)
			else:
				await member.remove_roles(role)
	@commands.command(help="Получить информацию об участнике", brief="Узнать участника", aliases=['gi', 'info'])
	async def getinfo(self, ctx, member:discord.Member=None):
		if member is None:
			member=ctx.author
		if not member.bot:
			global rates
			rating = 0
			cursor.execute(f"SELECT * FROM members where guildID={ctx.guild.id} and memberID={member.id}")
			result = cursor.fetchall()
			for row in result:
				rating = row[2]
				actions= row[3]
			index = round(rating*10/maxRate)-1
			if index<=0:
				index = 0
			elif index>=len(rates)-1:
				index=len(rates)-1
			embed=discord.Embed(title="Информация", description=f"У {member} `{rating}` баллов. Это {rates[index]}\nДоступно {actions} раз голосовать", color=0xFFFFFF)
			await ctx.send(embed=embed)
	@commands.command(help="Посмотреть список участников и их баллы", brief="Список", aliases=['list', 'top', 'gl'])
	async def getlist(self, ctx, page:int=1):
		memberlist = ""
		cursor.execute(f"SELECT * FROM members where guildID={ctx.guild.id} ORDER BY rating DESC")
		result = cursor.fetchall()
		if int(page)<=0:
			page = 1
		if page*10>len(result):
			for index in range(len(result)-len(result)%10, len(result)):
				memberlist = f"{memberlist}{index+1}. {self.client.get_user(result[index][1])} - `{result[index][2]}`.\n"
			embed=discord.Embed(title="Список:", description=f"{memberlist}[{round(len(result)/10)}/{round(len(result)/10)}]", color=0x00FFFF)
			await ctx.send(embed=embed)
		else:
			for index in range(page*10-10,page*10):
				memberlist = f"{memberlist}{index+1}. {self.client.get_user(result[index][1])} - `{result[index][2]}`.\n"
			embed=discord.Embed(title="Список:", description=f"{memberlist}[{page}/{round(len(result)/10)}]", color=0xFF5700)
			await ctx.send(embed=embed)
		#await ctx.send(")
	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		errorMessage=""
		with open('prefixes.json', 'r') as f: 
				prefixes = json.load(f) #load the json as prefixes
		if isinstance(error, commands.CommandOnCooldown):
			cooldown = 0
			cooldown = '{:.0f}'.format(error.retry_after)
			print(cooldown)
			errorMessage=(f'Не так быстро! Подожди {cooldown} секунд.')
			embed=discord.Embed(title="Ошибка", description=errorMessage, color=0xFF0000)
			await ctx.send(embed=embed)
		if isinstance(error, commands.MissingPermissions):
			errorMessage=(f"У тебя нет прав!")
			embed=discord.Embed(title="Ошибка", description=errorMessage, color=0xFF0000)
			await ctx.send(embed=embed)
		if isinstance(error, commands.MissingRequiredArgument):
			errorMessage=(f"Вы что-то упустили. Посмотрите как использовать команду с помощью {prefixes[str(ctx.guild.id)]}help [команда]")
			embed=discord.Embed(title="Ошибка", description=errorMessage, color=0xFF0000)
			await ctx.send(embed=embed)
		#raise error
	@commands.command(help="Обнулить баллы у всех участников", brief="Обнуление", aliases=['rs'])
	@commands.has_permissions(administrator=True)
	async def reset(self, ctx):
		cursor.execute(f"UPDATE members SET rating = 1500, actions = 5 where guildID = {ctx.guild.id}")
		conn.commit()
		embed=discord.Embed(title="Внимание", description=f"У всех участников баллы были обнулены", color=0xFF0000)
		await ctx.send(embed=embed)
	@commands.command(help="Изменить у всех участников баллы", brief="Глобальное изменение", aliases=['gc'])
	@commands.has_permissions(administrator=True)
	async def globalchange(self, ctx, rating:int = 1500):
		cursor.execute(f"UPDATE members SET rating = {rating} where guildID = {ctx.guild.id}")
		conn.commit()
		embed=discord.Embed(title="Внимание", description=f"У всех участников баллы изменены на `{rating}`", color=0xFF0000)
		await ctx.send(embed=embed)

	@commands.command()
	async def like(self, ctx, member:discord.Member):
		if not member.bot:
			if member.id == ctx.author.id:
				await ctx.send("Вы не можете давать или отнимать баллы у себя!")
			else:
				cursor.execute(f"SELECT * FROM members where guildID={ctx.guild.id} and memberID={ctx.author.id}")
				results = cursor.fetchall()
				for row in results:
					guild=row[0]
					user=row[1]
					rating=row[2]
					actions=row[3]
				cursor.execute(f"SELECT * FROM members where guildID={ctx.guild.id} and memberID={member.id}")
				results = cursor.fetchall()
				for row in results:
					memberRating=row[2]
				if actions>0:
					if (memberRating>0 and memberRating<maxRate):
						cursor.execute(f"UPDATE members SET actions=(actions-1) where memberID={ctx.author.id} and guildID={ctx.guild.id}")
						cursor.execute(f"UPDATE members SET rating=(rating+1) where memberID={member.id} and guildID={ctx.guild.id}")
						embed=discord.Embed(title=random.choice(positives), description=f"{ctx.author} оценил(-а) {member} положительно!", color=0x00FF00)
						await ctx.send(embed=embed)
						role = discord.utils.get(ctx.guild.roles, name="Нарушитель")
						if role is None:
							role = await ctx.guild.create_role(name="Нарушитель")
						if memberRating+1<1000:
							await member.add_roles(role)
						else:
							await member.remove_roles(role)
				else:
					rt=str(datetime.strptime('00:00:00','%H:%M:%S').strftime('%H:%M:%S'))
					now = datetime.now().strftime('%H:%M:%S')
					delta=datetime.strptime(rt,'%H:%M:%S')-datetime.strptime(now,'%H:%M:%S')
					delta=str(delta)[7:]
					embed=discord.Embed(title="Внимание", description=f"Вы достигли дневного ограничения! Дождитесь до завтра, осталось {delta}", color=0xFF0000)
					await ctx.send(embed=embed)
				conn.commit()
		
	@commands.command()
	async def dislike(self, ctx, member:discord.Member):
		if not member.bot:
			if member.id == ctx.author.id:
				await ctx.send("Вы не можете давать или отнимать баллы у себя!")
			else:
				cursor.execute(f"SELECT * FROM members where guildID={ctx.guild.id} and memberID={ctx.author.id}")
				results = cursor.fetchall()
				for row in results:
					guild=row[0]
					user=row[1]
					rating=row[2]
					actions=row[3]
				cursor.execute(f"SELECT * FROM members where guildID={ctx.guild.id} and memberID={member.id}")
				results = cursor.fetchall()
				for row in results:
					memberRating=row[2]
				if actions>0:
					if (memberRating>0 and memberRating<maxRate):
						cursor.execute(f"UPDATE members SET actions=(actions-1) where memberID={ctx.author.id} and guildID={ctx.guild.id}")
						cursor.execute(f"UPDATE members SET rating=(rating-1) where memberID={member.id} and guildID={ctx.guild.id}")
						embed=discord.Embed(title=random.choice(negatives), description=f"{ctx.author} оценил(-а) {member} отрицательно!", color=0xFF0000)
						await ctx.send(embed=embed)
						role = discord.utils.get(ctx.guild.roles, name="Нарушитель")
						if role is None:
							role = await ctx.guild.create_role(name="Нарушитель")
						if memberRating-1<1000:
							while role not in member.roles:
								await member.add_roles(role)
						else:
							while role in member.roles:
								await member.remove_roles(role)
				else:
					rt=str(datetime.strptime('00:00:00','%H:%M:%S').strftime('%H:%M:%S'))
					now = datetime.now().strftime('%H:%M:%S')
					delta=datetime.strptime(rt,'%H:%M:%S')-datetime.strptime(now,'%H:%M:%S')
					delta=str(delta)[7:]
					embed=discord.Embed(title="Внимание", description=f"Вы достигли дневного ограничения! Дождитесь до завтра, осталось {delta}", color=0xFF0000)
					await ctx.send(embed=embed)
				conn.commit()
	@commands.command(aliases=["prop"])
	async def propaganda(self, ctx):
		try:
			extensions=['png', 'bmp', 'jpg', 'jpeg']
			files=[]
			pictures=[]
			for extension in extensions:
				if len(glob.glob(f'images/*.{extension}'))>0:
					files.append(glob.glob(f'images/*.{extension}'))
			for file in files:
				for f in file:
					#f=f.replace("./", "")
					pictures.append(f)
			random_image = random.choice(pictures)
			await ctx.send(file=discord.File(random_image))
			print("Sent")
		except Exception as err:
			print(err)
		
	@commands.command(aliases=["stat", "statistics"])
	async def stats(self, ctx):
		try:
			ratingList=[]
			summ = 0
			cursor.execute(f"SELECT * FROM members where guildID={ctx.guild.id} ORDER BY rating DESC")
			results=cursor.fetchall()
			for row in results:
				ratingList.append((int(row[1]),int(row[2])))
			for member in ratingList:
				summ+=member[1]
			average=summ/len(ratingList)
			maxMember=ratingList[0]
			minMember=ratingList[-1]
			embed=discord.Embed(title="Информация", description=f"Средний балл по серверу - `{round(average,2)}`\nСамый высокий балл - {self.client.get_user(maxMember[0])}|`{maxMember[1]}`\nСамый низкий балл - {self.client.get_user(minMember[0])}|`{minMember[1]}`", color=0xFFFFFF)
			await ctx.send(embed=embed)
		except Exception as err:
			print(err)
			
	@commands.command(help = "Восхвалить партию", brief="Восхвалить партию",aliases=["pr"])
	async def praise(self, ctx):
		cursor.execute(f"SELECT * FROM members where guildID={ctx.guild.id} and memberID={ctx.author.id}")
		results = cursor.fetchall()
		for row in results:
			memberRating=row[2]
			actions=row[3]
		if actions>0:
			cursor.execute(f"UPDATE members SET actions=(actions-1) where memberID={ctx.author.id} and guildID={ctx.guild.id}")
			if random.randint(1,100)<=5:
				if (memberRating>0 and memberRating<maxRate):
					cursor.execute(f"UPDATE members SET rating=(rating+1) where memberID={ctx.author.id} and guildID={ctx.guild.id}")
				embed=discord.Embed(title=random.choice(positives), description=f"{ctx.author} восхваляет партию! И получает за это 1 социальный рейтинг.", color=0x00FF00)
				await ctx.send(embed=embed)
			else:
				embed=discord.Embed(title=random.choice(positives), description=f"{ctx.author} восхваляет партию!", color=0x00FF00)
				await ctx.send(embed=embed)
		else:
			rt=str(datetime.strptime('00:00:00','%H:%M:%S').strftime('%H:%M:%S'))
			now = datetime.now().strftime('%H:%M:%S')
			delta=datetime.strptime(rt,'%H:%M:%S')-datetime.strptime(now,'%H:%M:%S')
			delta=str(delta)[7:]
			embed=discord.Embed(title="Внимание", description=f"Вы достигли дневного ограничения! Дождитесь до завтра, осталось {delta}", color=0xFF0000)
			await ctx.send(embed=embed)
		conn.commit()

	@commands.command(help = "Очистить базу данных от участников которых нет в сервере", brief="Очистить бд от лишнего",aliases=["cl"])
	@commands.has_permissions(administrator=True)
	async def clear(self, ctx):
		try:
			usersInDataBase=[]
			usersInGuild=ctx.guild.members
			cursor.execute(f"SELECT * FROM members where guildID={ctx.guild.id}")
			results = cursor.fetchall()
			for row in results:
				usersInDataBase.append(row[1])
			for row in usersInDataBase:
				if self.client.get_user(row) in usersInGuild:
					usersInDataBase.remove(row)
			mlist=[row for row in usersInDataBase if self.client.get_user(row) not in usersInGuild]
			for row in mlist:
				cursor.execute(f"DELETE FROM members where guildID={ctx.guild.id} and memberID={row}")
			conn.commit()
			embed=discord.Embed(title="Внимание", description=f"Очищено {len(mlist)} строк.", color=0xFF0000)
			await ctx.send(embed=embed)
		except Exception as err:
			print(e)
		

def setup(client):
	client.add_cog(Manager(client))