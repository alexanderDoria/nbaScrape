
from time import sleep
from random import randint
from stats_utils import *
from scrape_utils import *
from pytz import timezone
from datetime import datetime
import pandas as pd

#if hour < 12: exit()

url = 'https://www.espn.com/nba/scoreboard'
#url = 'https://www.espn.com/nba/scoreboard/_/date/20200213'

# TODO: read static gamelogs from WZRD API

def scrape():
    games = get_games(url)
    
    print("games: ", games)

    print('calculating live games...')
    for g in games['live']:
        sleep(randint(5, 10))
        print("waiting...")
        process_gamelogs(g, url)
    print("done")

    print('calculating static games...')
    for g in games['static']:
        sleep(randint(5, 10))
        print("waiting...")
        process_gamelogs(g, url)
    print("done")

scrape()

print("logs: ", logs)

if len(logs) > 0:
    print(requests.post("https://bilalsattar24.pythonanywhere.com/nbastatline/", json={'gameLogs':logs}))
else:
    print("no logs")

#(optional) writre to csv
logs = pd.DataFrame(logs)
logs.to_csv("gamelogs.csv")
