from flask import Flask
from flask_restful import Resource, reqparse, Api
from flask_restful.utils import cors
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from uuid import uuid4
from datetime import datetime
import json, os
import argparse


parser = argparse.ArgumentParser()
parser.add_argument(dest='gamename', help="The Name of the Godot Game")
parser.add_argument('-i', '--ip', action="store", default='127.0.0.1', help="The listening IP Address")
parser.add_argument('-p', '--port', action="store", default='8000', help="The listening Port")


REST_API = Flask(__name__)
# Very basic DOS prevention
limiter = Limiter(
    REST_API,
    key_func=get_remote_address,
    default_limits=["90 per minute"]
)
api = Api(REST_API)
api.decorators=[cors.crossdomain(origin='*')]

games = {}

def write_to_disk():
	with open("games", 'w') as db:
		json.dump(games,db)


class NewGame(Resource):
	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument("game_name")
		parser.add_argument("deck")
		args = parser.parse_args()
		if args["game_name"] != stat_args.gamename:
			return("Wrong Game!", 403)
		game_id = str(uuid4())
		games[game_id] = {
			"start_datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			"deck": args["deck"],
			"state": "unfinished"
		}
		write_to_disk()
		return(game_id, 201)

class Game(Resource):
	def get(self, gameid):
		game_details = games.get(gameid)
		if game_details:
			return(game_details, 200)
		else:
			return("Game not found", 404)

	def put(self, gameid):
		parser = reqparse.RequestParser()
		parser.add_argument("state")
		parser.add_argument("details")
		args = parser.parse_args()
		if not games.get(gameid):
			return("Game ID not found", 404)
		elif games[gameid].get('state') != "unfinished":
			return("Game already resolved", 409)
		else:
			games[gameid]['state'] = args['state']
			games[gameid]['details'] = args['details']
			games[gameid]["end_datetime"]: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			write_to_disk()
			return(games[gameid], 200)

if os.path.isfile("games"):
	with open("games") as db:
		games = json.load(db)

# Parse and print the results
stat_args = parser.parse_args()

api.add_resource(Game, "/game/<string:gameid>")
api.add_resource(NewGame, "/newgame/")

REST_API.run(debug=True,host=stat_args.ip,port=stat_args.port)
