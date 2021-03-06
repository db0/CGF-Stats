from flask import Flask
from flask_restful import Resource, reqparse, Api
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from uuid import uuid4
from datetime import datetime
import json, os
import argparse
import threading, time

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument(dest='gamename', help="The Name of the Godot Game")
arg_parser.add_argument('-i', '--ip', action="store", default='127.0.0.1', help="The listening IP Address")
arg_parser.add_argument('-p', '--port', action="store", default='8000', help="The listening Port")
arg_parser.add_argument('--states', action="store", default='defeat,victory', help="Valid states for end-game submission")


REST_API = Flask(__name__)
# Very basic DOS prevention
limiter = Limiter(
	REST_API,
	key_func=get_remote_address,
	default_limits=["90 per minute"]
)
api = Api(REST_API)

games = {}
end_game_states = []

def write_to_disk():
	with open("games", 'w') as db:
		json.dump(games,db)


class GamePruner(object):
	# Every hour we delete all game which have been recorded unfinished for 5 hours or more.
	def __init__(self, interval = 3600, seconds_to_wait = 18000):
		self.interval = interval
		self.seconds_to_wait = seconds_to_wait

		thread = threading.Thread(target=self.prune_uncompleted_games, args=())
		thread.daemon = True
		thread.start()

	def prune_uncompleted_games(self):
		while True:
			pruned_count = 0
			for game in games.copy():
				if games[game]['state'] == "unfinished":
					start_time = datetime.strptime(games[game].get("start_datetime", ''), "%Y-%m-%d %H:%M:%S")
					if (datetime.now() - start_time).seconds >= self.seconds_to_wait:
						del games[game]
						pruned_count += 1
			if pruned_count >= 1:
				print(f" * Pruned {pruned_count} uncompleted games from the database", flush=True)
				write_to_disk()
			time.sleep(self.interval)


@REST_API.after_request
def after_request(response):
	response.headers["Access-Control-Allow-Origin"] = "*"
	response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT, DELETE"
	response.headers["Access-Control-Allow-Headers"] = "Accept, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization"
	return response


class NewGame(Resource):
	decorators = [limiter.limit("4/minute")]
	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument("game_name", type=str, required=True, help="Name has to be valid string")
		parser.add_argument("deck", type=dict, required=True, help="Has to be a dictionary")
		parser.add_argument("client", type=str, required=True, help="Name has to be valid string")
		args = parser.parse_args()
		if args["game_name"] != stat_args.gamename:
			return("Wrong Game!", 403)
		game_id = str(uuid4())
		games[game_id] = {
			"start_datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			"deck": args["deck"],
			"client": args["client"],
			"state": "unfinished"
		}
		write_to_disk()
		return(game_id, 201)

	def options(self):
		return("OK", 200)


class Game(Resource):
	def get(self, gameid):
		game_details = games.get(gameid)
		if game_details:
			return(game_details, 200)
		else:
			return("Game not found", 404)

	def put(self, gameid):
		parser = reqparse.RequestParser()
		parser.add_argument("state", type=str, required=True, help="Name has to be valid string")
		parser.add_argument("details", type=dict, required=False, help="Has to be a dictionary")
		args = parser.parse_args()
		if not games.get(gameid):
			return("Game ID not found", 404)
		elif games[gameid].get('state') != "unfinished":
			return("Game already resolved", 409)
		elif not args['state'] in end_game_states:
			return("Invalid end-game state", 403)
		else:
			games[gameid]['state'] = args['state']
			games[gameid]['details'] = args['details']
			games[gameid]["end_datetime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			write_to_disk()
			return(games[gameid], 200)

	def options(self, gameid):
		return("OK", 200)


if os.path.isfile("games"):
	with open("games") as db:
		games = json.load(db)

# Parse and print the results
stat_args = arg_parser.parse_args()

end_game_states = stat_args.states.split(',')
api.add_resource(Game, "/game/<string:gameid>")
api.add_resource(NewGame, "/newgame/")

GamePruner()
REST_API.run(debug=True,host=stat_args.ip,port=stat_args.port)
