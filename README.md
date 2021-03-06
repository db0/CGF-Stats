# Card Game Framework Game Stats

A basic REST API service to record and retrieve game stats from [Godot Card Game Framework](https://github.com/db0/godot-card-game-framework) games

*Requires Python3*

## Setup

Clone this repository from your server and run it

```python cgf-stats.py "My Cool Card Game" -i "your.ip.address"```

It will bring the REST API in port 8000

## Usage

In the Card Game Framework, edit your CFConst and add your server address and port to STATS_URI and STATS_PORT.

Whenever you start a new game, initiate the stats with:
```var stats = GameStats.new(deck)```

Where `deck` should be a dictionary with the deck contents being used

Whenever the game ends, finalize the game with

```stats.complete_game({"state": state, "details": details})```

Where `state` should be something like "victory" or "defeat". `details` is a dictionary with any additional details about the game you want to store. It will be inserted as it is into your game stats.

## Game Stats

The game stats are stored after each modification in the `games` file in the same directory as simple json. You can parse this file to compile stats from all the games played for your game until this point