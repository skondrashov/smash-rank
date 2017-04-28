import json
import pickle
import glicko2
import re
import operator
import Queue
from challonge import participants, matches, tournaments
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import WriteBrackets
import MySQLdb as mariadb
import string
import re
import pysmash
import math

''''''
# http://stackoverflow.com/questions/19201290/how-to-save-a-dictionary-to-a-file

# Update the pkl file
def saveObj(obj, path):
	with open(path, 'wb') as f:
		pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

# Return the data at path
def loadObj(path):
	with open(path, 'rb') as f:
		return pickle.load(f)	
''''''

class Match:
	def __init__(self, player1name, player1score, player2name, player2score):
		self.player1name = player1name
		self.player1score = player1score
		self.player2name = player2name
		self.player2score = player2score

class RaterSetup:
	
	def __init__(self, pathToPlayers, pathToMatches):
		
		self.db = mariadb.connect(host="localhost",
                     user="mingee",         # your username
                     passwd="",  # your password
                     db="MeleeData",         # name of the data base
                     use_unicode = True,
                     charset = "utf8")
		self.pathToPlayers = pathToPlayers
		self.pathToMatches = pathToMatches
		
		# Player names |-> Glicko2 Player objects
		self.players = {}
		self.playersInTournament = {}
		# Check is loadObj is a file. If so, then load the object. Otherwise start fresh lol.
		# 
		# self.players = loadObj(pathToPlayers)
		self.matches = []
		
		self.tournaments = []
		self.currentTID = 0
		self.bracket_size = 0.0
		currentTournament = []
		# Write to bracket URLs files
		# WriteBrackets.writeChallongeBracketURLs()
		# WriteBrackets.writeSmashGGBracketURLs()

		# Fill list of matches
		self.__setMatches()	
		cur = self.db.cursor()

		while self.tournaments:
			currentTournament = self.tournaments.pop(0)
	 		tournament_name = ''
	 		#Tournament is Challonge
			if currentTournament[1] == 'c':
				#self.bracket_size = 
				self.__setChallongeMatches(currentTournament[0])
				if('-' in currentTournament[0]):
					tournament_name = currentTournament[0].split('-')[1].lower()
					cur.execute("SELECT id FROM tournaments WHERE name = %s;", [tournament_name])
				else:		
					tournament_name = currentTournament[0]		
					cur.execute("SELECT id FROM tournaments WHERE name = %s;", [tournament_name])

			#Tournament is on Smash.GG
			else:
				self.bracket_size = self.__setSmashGGMatches(currentTournament[0])
				tournament_name = currentTournament[0].split("/tournament/")[1].split("/")[0]
				cur.execute("SELECT id FROM tournaments WHERE name = %s;", [tournament_name])
			print tournament_name
			print self.bracket_size
			result = cur.fetchone()
			self.currentTID = result[0]
			
			# Fill map of players to Glicko2 Player objects
			self.__setPlayers()

			# Write list of matches to text file	
			# self.__writeMatches()
			

			
			# Write file of player map (.pkl)
			self.__writePlayers()
			self.matches = []
		self.db.close()
	def getPlayerMap(self):
		return self.players	
		
	def __setMatches(self):
		minParticipants = 32
		# challongeTournamentIds = self.__getChallongeTournamentIds()
		# for tournament in challongeTournamentIds:
		# 	self.tournaments.append((tournament, 'c'))
		
		# smashGGTournamentURLs = self.__getSmashGGTournamentURLs()
		# for tournament in smashGGTournamentURLs:
		# 	self.tournaments.append((tournament, 's'))
		
		self.__getTournamentIds()

	def __getTournamentIds(self):


		tournamentIds = []
		with open("data/brackets.txt", "r") as f:
			for line in f:
				line = line.lower()
				name = line[8:].rstrip()
				if name.split('/')[0] == "smash.gg":
					self.tournaments.append((line.strip(), 's'))
				else:
					url = line.split(".")
					if url[1] == "challonge":
						name = line[7:].rstrip()
						challongetitle = name.split('.')[0]
						brackettitle = name.split('/')[1]
						self.tournaments.append((challongetitle + '-' + brackettitle, 'c'))
					else:
						name = line[21:].rstrip()
						self.tournaments.append(("" + name, 'c'))
			self.tournaments = filter(None, self.tournaments)
		return tournamentIds




	def __getChallongeTournamentIds(self):
		# Make a list of challonge tournament Ids
		challongeTournamentIds = []
		with open("data/challongeBracketURLs.txt", "r") as f:
			for line in f:
				url = line.split(".")
				if url[1] == "challonge":
					name = line[7:].rstrip()
					challongetitle = name.split('.')[0]
					brackettitle = name.split('/')[1]
					challongeTournamentIds.append(challongetitle + '-' + brackettitle)
				else:
					name = line[21:].rstrip()
					challongeTournamentIds.append("" + name)

		return challongeTournamentIds

	def __getSmashGGTournamentURLs(self):
		# Make a list of smashGG tournament URLs
		smashGGURLs = []
		f = open("data/smashGGBracketURLs.txt", "r")
		for line in f:
			line = line.lower()
			line = line.replace("-", "")
			smashGGURLs.append(line.strip())
		smashGGURLs = filter(None, smashGGURLs)
		return smashGGURLs

		
	# Purpose: Compile list of Match objects from Challonge
	# In:      tournamentIds - list of tournament names in format:
	# 		   michigansmash-<name>
	#		   tournaments must be in chronological order (oldest to youngest)
	#		   minParticipants - ignore tournaments with fewer participants
	# Out:	   List of Match objects of Challonge matches in chronological order
	#		   (oldest to youngest)
	def __setChallongeMatches(self, tournamentId):
		
		APIkey = "2tyMsGrcQanAq3EQeMytrsGrdMMFutDDz0BxNAAh"
		tournamentsURL = "https://Amirzy:" + APIkey + "@api.challonge.com/v1/tournaments/"
		
		# Create cursor to execute queries
		cur = self.db.cursor()

		# Construct list of Match objects from all tournaments


		#
		#
		#
		# Don't do it if you already have the tournament in the database ugh
		#
		#

		# Add the tournament to the database
		tournament_name = ''

		if('-' in tournamentId):
			tournament_name = tournamentId.split('-')[1].lower()
			q = (0, tournament_name, stripNum(tournament_name), 'Ann Arbor')	
			cur.execute("INSERT INTO tournaments (id, name, series, location, date) VALUES (%s, %s, %s, %s, default);", q)
		else:
			tournament_name = tournamentId
			q = (0, tournamentId, stripNum(tournamentId), 'Ann Arbor')	
			cur.execute("INSERT INTO tournaments (id, name, series, location, date) VALUES (%s, %s, %s, %s, default);", q)


		# A tournament participant is object w/ player id for this tournament
		participantsInTournament = requests.get(tournamentsURL + tournamentId + "/participants.json").json()

		# Maps player Ids to player names
		IdToPlayerName = {}
		partSize = 0
		# Compile id:name map

		cur.execute("SELECT id FROM tournaments WHERE name = %s;", [tournament_name])
		tournament_id = cur.fetchone()[0]
		for p in participantsInTournament:
			# Get playername
			partSize += 1
			playerName = p["participant"]["display_name"]
			playerName = playerName.lower()
			playerName = playerName.replace(" ", "")
			playerName = playerName.replace("\t", "")
			playerName = playerName.replace("(unpaid)", "")


			if ('|') in playerName:
				playerName = playerName.split('|')[-1]

			re.sub(r"[^\\x00-\\x7f]", "", playerName)
			playerName.replace(u"\u2122", '')
			#print playerName
			# Add to map
			IdToPlayerName[p["participant"]["id"]] = playerName



			cur.execute("SELECT id FROM players WHERE tag = %s;", [playerName])
			p1_id = cur.fetchone()

			if not p1_id:
				self.players[playerName] = glicko2.Player()
				p1 = (0, playerName)	
				cur.execute("INSERT INTO players (id, tag, sponsor, skill) VALUES (%s, %s, null, default);", p1)
							

			cur.execute("SELECT id FROM players WHERE tag = %s;", [playerName])
			player_id = cur.fetchone()[0]
			

			cur.execute("INSERT INTO attended (id, player_id, tournament_id) VALUES (%s, %s, %s);", [0, player_id, tournament_id])
			self.db.commit()
		self.bracket_size = partSize	
		# Dictionary from int index to json match objects
		jsonMatchesDict = requests.get(tournamentsURL + tournamentId + "/matches.json").json()
		
		# Turn the dict into a list
		jsonMatches = []
		for i in range(0, len(jsonMatchesDict)):
			jsonMatches.append(jsonMatchesDict[i]["match"])
		
		# Scores must be of the format ">-<"
		scoreFormat = re.compile("\d+-\d+")
		
		# Compile the list of Match objects
		for jsonMatch in jsonMatches:

			# Some scores are not of the right format, so skip these
			scoreStr = jsonMatch["scores_csv"]
			if not scoreFormat.match(scoreStr):
				return
			
			# Extract scores
			separatorIndex = scoreStr.index("-")
			player1score = int(scoreStr[:separatorIndex])
			player2score = int(scoreStr[separatorIndex+1:])
			
			# Extract names
			player1name = IdToPlayerName[jsonMatch["player1_id"]].lower()
			player2name = IdToPlayerName[jsonMatch["player2_id"]].lower()


			# Add all players to dictionary as unrated Glicko2 player objects, as well as the database

			
			newMatch = Match(player1name, player1score, player2name, player2score)
			self.matches.append(newMatch)

		

			# Use all the SQL you like


		# print all the first cell of all the rows
		self.db.commit()
		cur.close()
		
	# Purpose: Compile list of Match objects from SmashGG
	# In:      tournament_URLs - list of tournament URLs in format:
	# Out:	   List of Match objects of SmashGG matches in chronological order
	#		   (oldest to youngest)
	def __setSmashGGMatches(self, url):
		cur = self.db.cursor()
			#Smash.gg wrapper
		smash = pysmash.SmashGG()

		# Get tournament name

		tournament_name = url.split("/tournament/")[1].split("/")[0]


		#
		#
		# Ann Arbor should be replaced by region use tourney information to find venue address and get State from there. 
		#
		#
		p = (0, tournament_name, stripNum(tournament_name), 'Ann Arbor')	
		cur.execute("INSERT INTO tournaments (id, name, series, location, date) VALUES (%s, %s, %s, %s, default);", p)

		players = smash.tournament_show_players(tournament_name, 'melee-singles')


		# Add all players to database if they're not in there already
		for player in players:

			# Santitize tag of fuckery
			tag = player['tag'].lower()
			tag = tag.replace(" ", "")
			re.sub(r"[^\\x00-\\x7f]", "", tag)
			tag.replace(u"\u2122", '')
			#tag = str(tag.encode('ascii', 'replace'))
			cur.execute("SELECT * FROM players WHERE tag = %s;", [tag])
			result = cur.fetchone()

			# Add player to database
			if not result:	
				self.players[tag] = glicko2.Player()
				p = (0, tag, player['entrant_id'])	
				cur.execute("INSERT INTO players (id, tag, sponsor, smashgg_id, skill) VALUES (%s, %s, null, %s, default);", p)				
			else:
				p = (player['entrant_id'], tag)
				cur.execute("UPDATE players SET smashgg_id = %s WHERE tag = %s;", p)

			self.db.commit()
			cur.execute("SELECT id FROM players WHERE tag = %s;", [tag])
			player_id = cur.fetchone()[0]
			cur.execute("SELECT id FROM tournaments WHERE name = %s;", [tournament_name])
			tournament_id = cur.fetchone()[0]

			cur.execute("INSERT INTO attended (id, player_id, tournament_id) VALUES (%s, %s, %s);", [0, player_id, tournament_id])
		self.db.commit()

		# Split this into another function 
		sets = smash.tournament_show_sets(tournament_name, 'melee-singles')

		for match in sets:
			entrant1Id = match['entrant_1_id']
			entrant2Id = match['entrant_2_id']
			winner_id = match['winner_id']
			loser_id = match['loser_id']
			entrant1_tag = ''
			entrant2_tag = ''
			winner_tag = ''
			loser_tag = ''
			winner_set_count = 0
			loser_set_count = 0
			entrant1Score = match['entrant_1_score']
			entrant2Score = match['entrant_2_score']
			cur.execute("SELECT tag FROM players WHERE smashgg_id = %s;", [entrant1Id])
			entrant1_tag = cur.fetchone()[0]
			cur.execute("SELECT tag FROM players WHERE smashgg_id = %s;", [entrant2Id])
			entrant2_tag = cur.fetchone()[0]
	
			if entrant1_tag and entrant2_tag:
				entrant1_tag = entrant1_tag.lower()
				entrant1_tag = entrant1_tag.replace(" ", "")
				entrant2_tag = entrant2_tag.lower()
				entrant2_tag = entrant2_tag.replace(" ", "")
				newMatch = Match(entrant1_tag, entrant1Score, entrant2_tag, entrant2Score)
				self.matches.append(newMatch)
		
		self.db.commit()
		cur.close()

		return len(players)
	# Purpose: Write info of Match objects in txt file
	def __writeMatch(self, match):
		cur = self.db.cursor()
		cur.execute("SELECT id FROM players WHERE tag = %s;", [match.player1name])
		p1_id = cur.fetchone()[0]

		cur.execute("SELECT id FROM players WHERE tag = %s;", [match.player2name])
		p2_id = cur.fetchone()[0]
		if not (match.player1score == None or match.player2score == None):
			if match.player1score > match.player2score:
				data = (0, self.currentTID, p1_id, p2_id, match.player1score, match.player2score, 0, True)
				cur.execute("INSERT INTO sets (id, tournament_id, winner_id, loser_id, best_of, loser_wins, sets_remaining, is_losers) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);", data)
			else:
				data = (0, self.currentTID, p2_id, p1_id, match.player2score, match.player1score, 0, True)
				cur.execute("INSERT INTO sets (id, tournament_id, winner_id, loser_id, best_of, loser_wins, sets_remaining, is_losers) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);", data)

		self.db.commit()
		cur.close()








	# Purpose: Use this function once. It is for constructing the .pkl data file
	# 		   that will store the map of player names to ratings.
	# Out: 	   Dictionary of player names to glicko2.Player() objects. Every player
	#		   will have their glicko2 rating after all the matches seen.
	def __setPlayers(self):
		# cur = self.db.cursor()
		# tournmentName = tournamentId.split('-')[1].lower()
		# p = (0, tournmentName, stripNum(tournmentName), 'Ann Arbor')	
		# cur.execute("INSERT INTO tournaments (id, name, series, location, date) VALUES (%s, %s, %s, %s, default);", p)
		# self.db.commit()
		# cur.close()
		# self.db.close()

		cur = self.db.cursor()
		# cur.execute("SELECT P.skill FROM players P, attended A, tournaments T WHERE T.id = A.tournament_id AND P.id = A.player_id AND T.id = %s ORDER BY P.skill DESC;", [self.currentTID])
		# skill_list = cur.fetchall()
		# skill_sum = 0.0

		# skill_list = skill_list[0:4]

		# for person in skill_list:
		# 	skill_sum += person[0]
		# average_skill = skill_sum/len(skill_list)
		# if average_skill <= 1600:
		# 	print 1
		# 	average_skill = 1
		# elif average_skill <= 1800:
		# 	print 1.1
		# 	average_skill = 1.1
		# elif average_skill <= 2000:
		# 	print 1.3
		# 	average_skill = 1.3
		# elif average_skill <= 2200:
		# 	print 1.5
		# 	average_skill = 1.5
		# elif average_skill <= 2400:
		# 	print 1.8
		# 	average_skill = 1.8
		# elif average_skill <= 2600:
		# 	print 2.0
		# 	average_skill = 2.0
		# elif average_skill <= 2800:	
		# 	print 2.3
		# 	average_skill = 2.3
		# elif average_skill <= 3000:	
		# 	print 2.6
		# 	average_skill = 2.6
		# elif average_skill <= 3200:	
		# 	print 3.0
		# 	average_skill = 3.0
		# elif average_skill <= 3400:	
		# 	print 3.5
		# 	average_skill = 3.5

					# else:
		# 	average_skill = average_skill - 1500
		# 	average_skill /= 100
		# 	average_skill = math.sqrt(average_skill)
		# 	print average_skill
		# 	#print math.pow(math.log(average_skill-1500, 16), 4)

		# for k, v in self.players.items():

		# 	size = math.pow(math.log(self.bracket_size, 4) - 1, 2)
		# 	v.setSize(size)
		# 	v.setAvg(average_skill)
		
		for match in self.matches:

			p1name = match.player1name
			p2name = match.player2name
			p1score = match.player1score
			p2score = match.player2score

			self.__writeMatch(match)
			# Update both players ratings and rd's
			# There are no ties in matches
			temp = self.players[p1name]
			temp.update_player([self.players[p2name].getRating()], [self.players[p2name].getRd()], [p1score > p2score], 1)
			self.players[p2name].update_player([self.players[p1name].getRating()], [self.players[p1name].getRd()], [p1score < p2score], 1)
			self.players[p1name] = temp



			p1rating = self.players[p1name].getRating()
			p2rating = self.players[p2name].getRating()
			cur.execute("UPDATE players SET skill = %s WHERE tag = %s;", [p1rating, p1name])
			cur.execute("UPDATE players SET skill = %s WHERE tag = %s;", [p2rating, p2name])

			# Update the rating deviation of all other players
			for playerName in self.players:
				if playerName != p1name and playerName != p2name:
					self.players[playerName].did_not_compete()
		self.db.commit()
		cur.close()

	
	# Purpose: Persist the map of players
	def __writePlayers(self):
		selfref_list = [1, 2, 3]
		selfref_list.append(selfref_list)
		output = open(self.pathToPlayers, 'wb')
		pickle.dump(self.players, output)
		pickle.dump(selfref_list, output, -1)
		output.close()

	

def writeCSVofPlayers(pathToPlayersCSV, players):
	
	f = open(pathToPlayersCSV, "w")
	f.write("\"Name\",\"Rating\",\"Rating Deviation\",\"Volatility\"\n")
	for player in players:
		f.write("\"" + str(player) + "\",")
		f.write(str(players[player].getRating()) + ",")
		f.write(str(players[player].getRd()) + ",")
		f.write(str(players[player].getVol()) + "\n")
	f.close()

def stripNum(str_in):
    digit_list = "1234567890"
    for char in digit_list:
        str_in = str_in.replace(char, "")

    return str_in

def main():
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
	pathToMatches = "data/matches.txt"
	pathToPlayers = "data/players.pkl"
	
	# Will map names to glicko2.player()'s
	players = {}
	
	# Uncomment to construct all files from scratch and comment out the loadObj line
	players = RaterSetup(pathToPlayers, pathToMatches).getPlayerMap()
	players = loadObj(pathToPlayers)

	# pathToPlayersCSV = "data/players.csv"
	# writeCSVofPlayers(pathToPlayersCSV, players)

	#printTopN(100, players)
if __name__ == "__main__":
	main()