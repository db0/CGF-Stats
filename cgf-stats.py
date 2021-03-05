from flask import Flask
from flask_restful import Resource, reqparse, Api
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from uuid import uuid4
from datetime import datetime
import json, os

REST_API = Flask(__name__)
# Very basic DOS prevention
limiter = Limiter(
    REST_API,
    key_func=get_remote_address,
    default_limits=["120 per minute"]
)
api = Api(REST_API)

games = {}

def write_to_disk():
	with open("games", 'w') as db: 
		json.dump(games,db)
		

class NewGame(Resource):

	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument("deck")
		args = parser.parse_args()
		game_id = str(uuid4())
		games[game_id] = {
			"date": datetime.now().strftime("%Y-%m-%d"),
			"time": datetime.now().strftime("%H:%M:%S"),
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
		args = parser.parse_args()
		if not games.get(gameid):
			return("Game ID not found", 404)
		else:
			games[gameid]['state'] = args['state']
			write_to_disk()
			return(games[gameid], 200)

if os.path.isfile("games"):
	with open("games") as db: 
		games = json.load(db)
	
api.add_resource(Game, "/game/<string:gameid>")
api.add_resource(NewGame, "/newgame/")

REST_API.run(debug=True,port=8000)
