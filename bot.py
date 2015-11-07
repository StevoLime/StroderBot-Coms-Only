#Twitch chat bot code by Steven Anderson.
#Code is written in Python and is still being developed.
#If you use this code for a chat bot, please only change the variables that you need to change.
#If you want to add/remove commands and do not understand Python, please ask Steven.
#Each section of the code should have comments saying what it is.

#Importing modules for code.
import socket
import time
import re
import select
import requests
import urllib2
import json
import yaml
import thread
import threading
import sqlite3
import os
import ConfigParser
import random

#Importing variables file
conpar = ConfigParser.SafeConfigParser()
conpar.read('botvar.ini')

#Variables for bot. Text needs to be in ' ' but numbers do not.
#Variables needing to be modified should be located in the botvar.ini file.

server = 'irc.twitch.tv'						
port = 443										
nick = conpar.get("botname", "nick")							
oauth = conpar.get("botname", "oauth")							
channel = conpar.get("channelinfo", "channel")						
owner = conpar.get("channelinfo", "owner")								
rafact = 1
rdb = None
vernum = '1.0c'

#Connecting to Twitch irc server.
s = socket.socket()
s.connect((server, port))
s.send("PASS %s\r\n" % (oauth))
s.send("NICK %s\r\n" % nick)
s.send("USER %s\r\n" % (nick))
s.send("CAP REQ :twitch.tv/membership \r\n")
s.send("JOIN %s\r\n" % channel)

print "Connected to channel %s" % channel


#Function to check if command database is there and create if necessary.
def comdbexists():

	if os.path.exists('custcoms.db'):
		print "Coms Database is there."
		
	else:
		comdbconn = sqlite3.connect('custcoms.db')
		comdbcur = comdbconn.cursor()
		comdbcur.execute("CREATE TABLE Comsdb(com TEXT, lvl TEXT, commsg TEXT)")

		comdbconn.commit()
		comdbconn.close()
		print "Created Coms Database"

#Run command database check.
comdbexists()

#Connect to command database
comconn = sqlite3.connect('custcoms.db')
comcur = comconn.cursor()


print "Bot Started"

#Twitch api array pull. modlist is for mod commands. comuser is for command user. modlistd, userlist, and tstafflist is for the Point System.
def modlist():
	tapi = 'https://tmi.twitch.tv/group/user/%s/chatters' % owner
	response = urllib2.urlopen(tapi)
	tapiinfo = yaml.load(response)
	return tapiinfo["chatters"]["moderators"]

def modlistd():
	tdapi = 'https://tmi.twitch.tv/group/user/%s/chatters' % owner
	dresponse = urllib2.urlopen(tdapi)
	tdapiinfo = json.load(dresponse)
	return tdapiinfo["chatters"]["moderators"]
	
def userlist():
	tuapi = 'https://tmi.twitch.tv/group/user/%s/chatters' % owner
	uresponse = urllib2.urlopen(tuapi)
	tuapiinfo = json.load(uresponse)
	return tuapiinfo["chatters"]["viewers"]
	
def tstafflist():
	tsapi = 'https://tmi.twitch.tv/group/user/%s/chatters' % owner
	tsresponse = urllib2.urlopen(tsapi)
	tsapiinfo = json.load(tsresponse)
	
	stafflist = tsapiinfo["chatters"]["staff"]
	adminslist = tsapiinfo["chatters"]["admins"]
	gmodslist = tsapiinfo["chatters"]["global_mods"]
	
	combinedlist = stafflist + adminslist + gmodslist
	return combinedlist

def comuser():
	complete = msg[1: ].split(":", 1) # Parse the message into useful data sender[0] is username
	info = complete[0].split(" ")
	msgpart = complete[1]
	sender = info[0].split("!")
	return sender[0]



#Commands for bot. Do not change, remove, or add unless you understand the command setup.
#Custom commands can be added or removed using the addcomd and delcomd commands respectfully.
while(1):
	msg = s.recv(1024)
	#print msg
	
	if msg.find('PING') != -1:
		s.send('PONG ' + msg.split()[1] + '\r\n')

	if msg.find('PRIVMSG') != -1:
		tmp = msg.split('PRIVMSG')[-1]
		
		if tmp.find('!') != -1:
			regex = re.compile("(!\S*)")
			r = regex.findall(tmp)
			#check com database
			comr = r[0]
			comdbr = 'SELECT * FROM Comsdb WHERE com="%s"' % comr
			comcur.execute(comdbr)
			comdbf = comcur.fetchone()
			if comdbf is not None:
				rdb = comdbf[0]
				#print rdb
			for i in r:
				if i == '!notice':
					if comuser() == 'stevolime':
						s.send("PRIVMSG %s :Senpai noticed me!\r\n" % channel)
				
				#bot info
				elif i == "!version":
					s.send("PRIVMSG %s :Version %s. Written in Python.\r\n" % (channel, vernum))
				elif i == "!botinfo":
					s.send("PRIVMSG %s :This bot is using the StroderBot software in development by StevoLime using python and is on Version %s.\r\n" % (channel, vernum))
				
				#raffle commands
				elif i == "!vwrraf":
					if comuser() in modlist():
						if rafact == 1:
							vrtwapi = 'https://tmi.twitch.tv/group/user/%s/chatters' % owner
							vrtwresponse = urllib2.urlopen(vrtwapi)
							vrtwapilist = yaml.load(vrtwresponse)
							
							vrmodsu = vrtwapilist["chatters"]["moderators"]
							vrmodsu.remove(owner)
							vrmodsu.remove(nick)
							vrstaff = vrtwapilist["chatters"]["staff"]
							vradmins = vrtwapilist["chatters"]["admins"]
							vrgmods = vrtwapilist["chatters"]["global_mods"]
							vrviewers = vrtwapilist["chatters"]["viewers"]
							vrusrlst = vrmodsu + vrstaff + vradmins + vrgmods + vrviewers
							vrlstlen = len(vrusrlst)
							if vrlstlen > 1:
								vrranmax = vrlstlen - 1
							else:
								vrranmax = vrlstlen
							vrnum = random.randrange(0,vrranmax)
							vrwin = vrusrlst[vrnum]
							vrwinapi = 'https://api.twitch.tv/kraken/users/%s/follows/channels/%s' % (vrwin, owner)
							vrwinresp = requests.get(vrwinapi)
							vrwininfo = vrwinresp.json()
							
							if "message" in vrwininfo:
								s.send("PRIVMSG %s :Raffle winner is %s, and they ARE NOT a follower. BibleThump\r\n" % (channel, vrwin))
							else:
								s.send("PRIVMSG %s :Raffle winner is %s, and they are a follower. deIlluminati\r\n" % (channel, vrwin))	
						else:
							s.send("PRIVMSG %s :Raffle is already active.\r\n" % channel)
							
				#custom commands
				elif i == "!addcomd":
					if comuser() in modlist():
						ncall = tmp.split('|')
						if len(ncall) == 4:
							nccomm = ncall[1].lstrip()
							nccom = nccomm.rstrip()
							nclvll = ncall[2].lstrip()
							nclvl = nclvll.rstrip()
							ncmsgg = ncall[3].lstrip()
							ncmsg = ncmsgg.rstrip()
		
							acomsql = 'SELECT * FROM Comsdb WHERE com="%s"' % (nccom)
							comcur.execute(acomsql)
							actest = comcur.fetchone()
		
							if actest == None:
								comcur.execute("INSERT INTO Comsdb VALUES(?, ?, ?);", (nccom, nclvl, ncmsg))
								comconn.commit()
								s.send("PRIVMSG %s :Command has been added.\r\n" % channel)
						else:
							s.send("PRIVMSG %s :Not enough info for command. Please try again.\r\n" % channel)
			
				elif i == "!delcomd":
					if comuser() in modlist():
						dcall = tmp.split('|')
						if len(dcall) == 2:
							dccn = dcall[1]
							dccomm = dccn.lstrip()
							dccom = dccomm.rstrip()
		
							dcomsql = 'SELECT * FROM Comsdb WHERE com="%s"' % (dccom)
							comcur.execute(dcomsql)
							dctest = comcur.fetchone()
		
							if dctest is not None:
								delcomsql = 'DELETE FROM Comsdb WHERE com="%s"' % (dccom)
								comcur.execute(delcomsql)
								comconn.commit()
								s.send("PRIVMSG %s :Command has been removed.\r\n" % channel)
								
						else:
							s.send("PRIVMSG %s :No command specified. Please try again.\r\n" % channel)
							
				elif i == rdb:
					comusernc = comuser()
					if comdbf is not None:
						comlvl = comdbf[1]
						if comlvl == 'ol':
							if comusernc == owner:
								s.send("PRIVMSG %s :%s\r\n" % (channel, comdbf[2]))
						elif comlvl == 'ml':
							if comusernc in modlist():
								s.send("PRIVMSG %s :%s\r\n" % (channel, comdbf[2]))
						elif comlvl == 'vl':
							s.send("PRIVMSG %s :%s\r\n" % (channel, comdbf[2]))

				