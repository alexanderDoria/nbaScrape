from lxml import html
import requests
from time import sleep
from random import randint
from requests_html import HTMLSession
import numpy as np
from stats_utils import *
from pytz import timezone
from datetime import datetime
import pandas as pd

tz = timezone('America/Los_Angeles')
hour = datetime.now(tz).hour

#if hour < 8: exit()

image_url_sample = "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/[id].png"

logs = []
sorted_logs = []
categories = ['pts', 'reb', 'ast', 'stl', 'blk']
stats = {}
player_urls = {}

url = 'https://www.espn.com/nba/scoreboard/_/date/20191227'

# TODO: read static gamelogs from WZRD API

def get_today(url):
    if 'date' in url:
        today = url.split('/')[-1]
        return today[0:4] + '-' + today[4:6] + "-" + today[6:8]
    else:
        return datetime.now(tz).strftime('%Y-%m-%d')

def get_tree(url, page='html'):
    """returns tree from url depending on html or js content"""
    if page == 'js':
        while True:
            try:
                session = HTMLSession()
                print("fetching response...")
                resp = session.get(url)
                print("rendering JS...")
                resp.html.render()
                print("extracting html...")
                return html.fromstring(resp.html.html)
            except Exception as ex:
                print("failed")
                #print("error: ", ex)
                print("waiting...")
                sleep(randint(5, 10))
                print("retrying...")
    page = requests.get(url)
    return html.fromstring(page.content)


def is_live(s):
    """determines live status of a game table header"""
    s = s.lower()
    if 'final' in s or 'pt' in s:
        return False
    return True


def is_stat_row(r):
    r = r.lower()
    stop_words = ['starters', 'bench', 'team', 'dnp', '%']
    if any(s in r for s in stop_words):
        return False
    return True


def parse_name(name):
    """parses name of row name by excluding position and halving cell string"""
    for n in range(len(name)-1, 0, -1):
        if name[n].lower() == name[n]:
            name = name[0:(int((n+1)/2))]
            return name


def get_games(url):
    """searches NBA ESPN and returns live and static game urls"""
    print("scraping: ", url)
    urls = {}
    tree = get_tree(url, 'js')
    games = tree.xpath(
        '//*[@class="scoreboard-top no-tabs"]//table//thead//*[@class="date-time"]')
    games = [g.text_content() for g in games]
    boxscores = tree.xpath(
        '//*[@class="scoreboard-top no-tabs"]//*[@class="sb-actions"]//@href')
    boxscores = ['https://www.espn.com' +
                 b for b in boxscores if 'boxscore' in b]
    try:
        urls['live'] = [boxscores[i]
                        for i, s in enumerate(games) if is_live(s)]
    except:
        print("no live games")
    try:
        urls['static'] = [boxscores[i]
                          for i, s in enumerate(games) if not is_live(s)]
    except:
        print("no static games")
    print("success")
    #print("urls: ", urls)
    return urls


def get_team_info(tree, locale):
    team = {}
    if locale == "away":
        team['city'] = tree.xpath('//*[@class="team away"]//*[@class="long-name"]//text()')[0]
        team['team'] = tree.xpath('//*[@class="team away"]//*[@class="short-name"]//text()')[0]
        team['abbrev'] = tree.xpath('//*[@class="team away"]//*[@class="abbrev"]//text()')[0]
        team['score'] = tree.xpath('//*[@class="team home"]//*[@class="score-container"]//text()')[0]
    if locale == "home":
        team['city'] = tree.xpath('//*[@class="team home"]//*[@class="long-name"]//text()')[0]
        team['team'] = tree.xpath('//*[@class="team home"]//*[@class="short-name"]//text()')[0]
        team['abbrev'] = tree.xpath('//*[@class="team home"]//*[@class="abbrev"]//text()')[0]
        team['score'] = tree.xpath('//*[@class="team home"]//*[@class="score-container"]//text()')[0]
    return team


def create_id(name, team):
    name = name.replace(' ', '')
    name = name.replace('.', '')
    name = name.replace('-', '')
    name = name + team['abbrev']
    return name


def create_img_url(url):
    id = url.split('/')[-2]
    try: int(id)
    except: return
    return image_url_sample.replace('[id]', id)

def calc_pct(stat):
    try:
        m = int(stat.split('-')[0])
        a = int(stat.split('-')[1])
        return str(round(m / a, 2))
    except:
        return '0.00'

def count_doubles(log):
    counter = 0
    if int(log['pts']) > 10: counter += 1
    if int(log['reb']) > 10: counter += 1
    if int(log['ast']) > 10: counter += 1
    if int(log['stl']) > 10: counter += 1
    if int(log['blk']) > 10: counter += 1
    return counter

def get_log(r, locale, team):
    """takes gamelog table row and extracts each stat"""
    log = {}
    log['name'] = parse_name(r.xpath(
        './/*[@class="name"]')[0].text_content())
    log['position'] = r.xpath(
        './/*[@class="name"]//*[@class="position"]')[0].text_content()
    log['team'] = team[locale]['team']
    log['playerID'] = create_id(log['name'], team[locale])
    log['date'] = today
    log['location'] = team[locale]['city']
    if locale == "home": log['opponent'] = team['away']['team']
    else: log['opponent'] = team['home']['team']
    home_score = team['home']['abbrev'] + " " + team['home']['score']
    away_score = team['away']['abbrev'] + " " + team['away']['score']
    log['score'] = home_score + " | " + away_score
    log['min'] = r.xpath('.//*[@class="min"]')[0].text_content()
    #log['fg'] = r.xpath('.//*[@class="fg"]')[0].text_content()
    #log['3pt'] = r.xpath('.//*[@class="3pt"]')[0].text_content()
    ft = r.xpath('.//*[@class="ft"]')[0].text_content()
    log['ftm'] = ft.split('-')[0]
    log['fta'] = ft.split('-')[1]
    log['ftpct'] = calc_pct(ft)
    fg = r.xpath('.//*[@class="fg"]')[0].text_content()
    log['fgm'] = fg.split('-')[0]
    log['fga'] = fg.split('-')[1]
    log['fgpct'] = calc_pct(fg)
    threes = r.xpath('.//*[@class="3pt"]')[0].text_content()
    log['threepm'] = threes.split('-')[0]
    log['threepa'] = threes.split('-')[1]
    log['threepct'] = calc_pct(threes)
    log['oreb'] = r.xpath('.//*[@class="oreb"]')[0].text_content()
    log['dreb'] = r.xpath('.//*[@class="dreb"]')[0].text_content()
    log['reb'] = r.xpath('.//*[@class="reb"]')[0].text_content()
    log['ast'] = r.xpath('.//*[@class="ast"]')[0].text_content()
    log['stl'] = r.xpath('.//*[@class="stl"]')[0].text_content()
    log['blk'] = r.xpath('.//*[@class="blk"]')[0].text_content()
    log['to'] = r.xpath('.//*[@class="to"]')[0].text_content()
    log['pf'] = r.xpath('.//*[@class="pf"]')[0].text_content()
    log['plusminus'] = r.xpath(
        './/*[@class="plusminus"]')[0].text_content()
    log['pts'] = r.xpath('.//*[@class="pts"]')[0].text_content()
    doubles = count_doubles(log)
    log['td'] = 0
    log['dd'] = 0
    if doubles == 2:
        log['dd'] = 1
    if doubles == 3:
        log['td'] = 1
        
    log['image_url'] = create_img_url(player_urls[log['name']])
    log['value'] = value_log(log)
    return log


def calculate_stats():
    """calcuates mean and std of each category"""
    for c in categories:
        stats[c]['std'] = np.std(stats[c]['data'])
        stats[c]['mean'] = np.mean(stats[c]['data'])


def rank_log(log):
    """adds z-score value to each log"""
    val = 0
    for c in categories:
        val += (log[c] - stats[c]['mean']) / stats[c]['std']
        log['z'] = val

    for z in range(0, len(sorted_logs)):
        if val < sorted_logs[z]['z']:
            break

    sorted_logs.insert(log, z)


def rank_logs():
    """ranks logs by iterating and passing to rank_log()"""
    for log in logs:
        rank_log(log)

def update_player_urls(tree):
    names = tree.xpath('//*[@class="name"]//*[@class="abbr"]//text()')
    urls = tree.xpath('//*[@class="name"]//@href')

    print("names: ", names)
    print("player_urls: ", player_urls)

    for n in range(0, len(names)):
        player_urls[names[n]] = urls[n]
    

def process_gamelogs(url):
    """takes gamelog url and parses gamelogs and adds them to data structures"""
    print("processing: ", url)
    tree = get_tree(url, 'html')

    team_info = {}

    update_player_urls(tree)

    rows_home = tree.xpath('//*[@id = "gamepackage-boxscore-module"]//*[@class="col column-two gamepackage-home-wrap"]//table//tr')
    rows_away = tree.xpath('//*[@id="gamepackage-boxscore-module"]//*[@class="col column-one gamepackage-away-wrap"]//table//tr')
    
    rows_home = [r for r in rows_home if is_stat_row(r.text_content())]
    rows_away = [r for r in rows_away if is_stat_row(r.text_content())]

    team_info['home'] = get_team_info(tree, "home")
    team_info['away'] = get_team_info(tree, "away")

    for r in rows_home:
        log = get_log(r, "home", team_info)
        print("log: ", log)
        logs.append(log)

    for r in rows_away:
        log = get_log(r, "away", team_info)
        print("log: ", log)
        logs.append(log)


games = get_games(url)
today = get_today(url)

print("games: ", games)

for g in games['live']:
    print('calculating live games...')
    process_gamelogs(g)
    sleep(randint(5, 10))

for g in games['static']:
    print('calculating static games...')
    process_gamelogs(g)
    sleep(randint(5, 10))
    exit()

logs = pd.DataFrame(logs)
logs.to_csv("gamelogs.csv")

# calculate_stats()
# rank_logs()

#print("sorted logs: ", sorted_logs)
