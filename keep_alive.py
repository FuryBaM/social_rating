from flask import Flask, render_template, send_file, request
from threading import Thread
import sqlite3
from tabulate import tabulate
import webbrowser
from IPython.core.display import display,HTML
import discord, os
from discord.ext import commands
intents = discord.Intents.all()
client = discord.Client(intents=intents)
conn=sqlite3.connect("database.db", check_same_thread=False)
cursor=conn.cursor()

app=Flask("")
@app.route("/", methods=['GET', 'POST'])
def helloworld():
	guilds=client.guilds
	print("Server alive")
	cursor.execute(f"SELECT * FROM members")
	results=cursor.fetchall()
	return render_template("helloworld.html", data=list(results))

@app.route('/download')
def download_file():
	p="database.db"
	return send_file(p, as_attachment=True)

def run():
  app.run(host="0.0.0.0", port=8080)

def keep_alive():
  t = Thread(target=run)
  t.start()