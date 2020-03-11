
from time import sleep
from random import randint
from stats_utils import *
from scrape_utils import *
from pytz import timezone
from datetime import datetime
import pandas as pd

tz = timezone('America/Los_Angeles')
hour = datetime.now(tz).hour

if hour < 11 or hour >= 23: exit()

today = datetime.now(tz).strftime("%Y%m%d")
url = 'https://www.espn.com/nba/schedule/_/date/' + today

def scrape():
    games = get_games_live(url)
    
    print("games: ", games)

    print('scraping games...')
    for g in games:
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

print("scrape done, sleeping...")
sleep(randint(20, 30))