from time import sleep
from stats_utils import *
from scrape_utils import *
from pytz import timezone
from datetime import datetime, date, timedelta
import pandas as pd

start_date = date(2019, 10, 22)
end_date = date(2019, 11, 1)

url = 'https://www.espn.com/nba/scoreboard/_/date/'

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def scrape(url):
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


for single_date in daterange(start_date, end_date):
    d = single_date.strftime("%Y%m%d")
    url_d = url + d
    today = get_today(url_d)
    scrape(url_d)
    print("logs: ", logs)
    if len(logs) > 0:
        print(requests.post("https://bilalsattar24.pythonanywhere.com/nbastatline/", json={'gameLogs':logs}))
    logs.clear()


#(optional) write to csv
#logs = pd.DataFrame(logs)
#logs.to_csv("gamelogs.csv")


#print("sorted logs: ", sorted_logs)
