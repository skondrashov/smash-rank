import json
import glicko2
import re
import operator
import Queue
#from challonge import participants, matches, tournaments
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import WriteBrackets
import MySQLdb as mariadb
import string
import re
import pysmash
import math

def prompt(type, value):
	return input("Retrieved "+type+": "+value+". Press Enter if this is correct or type the correct value:\n\t") or value

def strip_tag(tag):
	return "".join(c for c in tag if c.isalnum()).lower()

db_connection = mariadb.connect(
		user="root",
		passwd="paradise",
		database="MeleeData",
		host="localhost",
		use_unicode = True,
		charset = "utf8"
	)
db_cursor = db_connection.cursor()

matches = []
players = {}
for url in open('data/brackets.txt', 'r'):
	url = url.lower().replace('http://', '').replace('https://', '')

	tournament = {}
	with url.split('/')[0].split('.') as hostname_parts:
		host = hostname_parts[-2]

		if host == "challonge":
			tournament['id_string'] = (hostname_parts[0] + '-' + url.split('/')[1]).lower()
		else:
			print("Bad URL in input: " + url)
	tournament['host'] = host

	print("Loading tournament: " + tournament['id_string'])

	# skip existing
	db_cursor.execute("SELECT 1 FROM tournaments WHERE id_string = %s LIMIT 1", [tournament['id_string']])
	if db_cursor.fetchone() is not None:
		print("Tournament already saved in database; skipping.\n")
		continue

	if host == "challonge":
		data = {}
		try:
			for data_type, subpath in [(t, tournament['id_string']+s) for t,s in [('tournament',''),('matches','/matches'),('participants','/participants')]]:
				uri = 'https://api.challonge.com/v1/tournaments/'+subpath+'.json'
				print("Contacting API at %s..." % uri)
				data[data_type] = requests.get(uri+'?api_key=XBFwcbaWSvrfHiaNONNgwyfPo8LrYozALwIWfkBd').json()
		except Exception as e:
			print("Error accessing %s." % uri)
			print(e)
			continue

		with data['tournament']['tournament'] as t:
			tournament['name'] = prompt('name', t['name'])
			tournament['date'] = prompt('date', t['started_at'].split('T')[0])

		series_parts = tournament['name'].rsplit(None, 1)
		if len(series_parts) == 2 and all(c in '0123456789XVI' for c in series_parts[1]):
			series = series_parts[0]
		else:
			series = ''
		tournament['series'] = prompt('series', series)

		tournament['entrants'] = data['tournament']['participants_count']
		if tournament['entrants'] != len(data['participants']):
			print("Error: Only " + len(data['participants']) + " out of " + tournament['entrants'] + "  entrants have data.")
			return

		for player in data['participants']:
			player = player['participant']
			display_name = participant['name']
			sponsor, tag = display_name.split('|') if '|' in display_name else (None, display_name)
			players[strip_tag(tag)] = {'display_name': display_name, 'sponsor': sponsor}

	with tournament as t:
		db_cursor.execute("""
			INSERT INTO tournaments (id_string,      host,      name,      series,      date,     location)
			VALUES                  ('%s',           '%s',      '%s',      '%s',        '%s',     'MI')
			""",                    (t['id_string'], t['host'], t['name'], t['series'], t['date']))
	db_connection.commit()
	print("Inserted tournament data:")
	print(tournament)

	db_cursor.execute("""
		SELECT id, display_name, tag, rating, rating_deviation, volatility
		FROM players
		WHERE tag IN (%s)""", [','.join(['"' + tag + '"' for tag in players.keys()])])

	for player_id, display_name, tag, rating, rating_deviation, volatility in db_cursor.fetchall():
		player = players[tag]
		if display_name != player.display_name:
			db_cursor.execute("""
				UPDATE players SET (sponsor,        display_name)
				VALUES             ('%s',           '%s')              WHERE id = %s)
				""",               (player.sponsor, player.display_name,          player_id))
			db_connection.commit()
			print("Player %s updated to: %s" % (display_name, player.display_name))
		players.glicko2 = glicko2.Player(rating, rating_deviation, volatility)

	for tag in players.keys():
		player = players[tag]
		if player.glicko2:
			continue
		player.glicko2 = glicko2.Player()

		with player as p:
			with p.glicko2 as g2:
				db_cursor.execute("""
					INSERT INTO players (sponsor,   tag,  display_name,   rating,    rating_deviation, volatility)
					VALUES              ('%s',      '%s', '%s',           %s,        %s,               %s)
					""",                (p.sponsor, tag,  p.display_name, g2.rating, g2.rd,            g2.vol))
		db_connection.commit()
		print("New player added to database: %s" % player.display_name)

	scoreFormat = re.compile("\d+-\d+")
	for match in data['matches']:
		match = match['match']

		# scores in the wrong format are DQs and do not count for rating
		if not scoreFormat.match(match['scores_csv']):
			continue

		p1_score, p2_score = match['scores_csv'].split('-')
		p1_tag = strip_tag(match['player1_id'])
		p2_tag = strip_tag(match['player2_id'])
		matches.append({
				'p1': {
					'tag':   p1_tag,
					'score': p1_score
				},
				'p2': {
					'tag':   p2_tag,
					'score': p2_score
				}
			})

		db_cursor.execute("""
			INSERT INTO sets (tournament_id, winner_id, loser_id, best_of, loser_wins, sets_remaining, is_losers)
			VALUES           (%s, %s, %s, %s, %s, %s, %s)
			""", ())

		data = (0, self.currentTID, p2_id, p1_id, match.player2score, match.player1score, 0, True)
		self.db_cursor.execute("INSERT INTO sets (id, tournament_id, winner_id, loser_id, best_of, loser_wins, sets_remaining, is_losers) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);", data)

		self.db.commit()

	# Purpose: Use this function once. It is for constructing the .pkl data file
	# 		   that will store the map of player names to ratings.
	# Out: 	   Dictionary of player names to glicko2.Player() objects. Every player
	#		   will have their glicko2 rating after all the matches seen.
	def __setPlayers(self):
		# cur = self.db.cursor()
		# tournmentName = tournamentId.split('-')[1].lower()
		# p = (0, tournmentName, stripNum(tournmentName), 'Ann Arbor')
		# db_cursor.execute("INSERT INTO tournaments (id, name, series, location, date) VALUES (%s, %s, %s, %s, default);", p)
		# self.db.commit()
		# db_cursor.close()
		# self.db.close()

		# db_cursor.execute("SELECT P.skill FROM players P, attended A, tournaments T WHERE T.id = A.tournament_id AND P.id = A.player_id AND T.id = %s ORDER BY P.skill DESC;", [self.currentTID])
		# skill_list = db_cursor.fetchall()
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
			self.db_cursor.execute("UPDATE players SET skill = %s WHERE tag = %s;", [p1rating, p1name])
			self.db_cursor.execute("UPDATE players SET skill = %s WHERE tag = %s;", [p2rating, p2name])

			# Update the rating deviation of all other players
			for playerName in self.players:
				if playerName != p1name and playerName != p2name:
					self.players[playerName].did_not_compete()
		self.db.commit()


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