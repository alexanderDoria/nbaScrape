from lxml import html
import requests
from time import sleep, strptime
from random import randint
from requests_html import HTMLSession
import numpy as np
from stats_utils import *
from pytz import timezone
from datetime import datetime, date
import pandas as pd
import calendar

image_url_sample = "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/[id].png"

logs = []
sorted_logs = []
stats = {}
player_urls = {}


def get_today(url):
    if 'date' in url:
        today = url.split('/')[-1]
        return today[0:4] + '-' + today[4:6] + "-" + today[6:8]
    else:
        return datetime.now(tz).strftime('%Y-%m-%d')

def get_today_readable(url):
    if 'date' in url:
        today = url.split('/')[-1]
        return calendar.month_name[int(today[4:6])] + " " + today[6:8]
    else:
        return datetime.now(tz).strftime("%B %d")

def get_tree(url, page='html'):
    """returns tree from url depending on html or js content"""
    tries = 0
    if page == 'js':
        while tries < 4:
            try:
                session = HTMLSession()
                print("fetching response...")
                resp = session.get(url)
                print("rendering JS...")
                resp.html.render(timeout=30)
                print("closing session...")
                session.close()
                print("extracting html...")
                return html.fromstring(resp.html.html)
            except Exception as ex:
                print("failed")
                print("error: ", ex)
                print("waiting...")
                sleep(randint(5, 10))
                print("retrying...")
                tries += 1
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
    if name[len(name)-2:len(name)] in ('PG', 'SF', 'SG', 'PF'):
        return name[0:int(len(name)/2)-1]
    if name[len(name)-1:len(name)] in ('C', 'F', 'G'):
        return name[0:int(len(name)/2)]
    for n in range(len(name)-1, 0, -1):
        if name[n].lower() == name[n]:
            name = name[0:(int((n+1)/2))]
            return name

def get_games_live(url):
    tables = []
    game_urls = []

    tree = get_tree(url)

    schedule = tree.xpath('//*[@id="sched-container"]')[0]
    today_readable = get_today_readable(url)
    
    date_found = False
    for s in schedule.getchildren():
        if s.tag == 'h2' and today_readable not in s.text:
            break
        elif s.tag == 'h2' and today_readable in s.text:
            date_found = True
        if s.tag == "div" and date_found:
            tables.append(s)

    for t in tables:
        urls = t.xpath('.//tr//a//@href')
        game_urls.extend(['https://www.espn.com/nba/boxscore?gameId=' + u.split('=')[1] for u in urls if 'gameId' in u])
    return game_urls


def get_games(url):
    """searches NBA ESPN and returns live and static game urls"""
    print("scraping: ", url)
    urls = {}
    tree = get_tree(url, 'js')
    
    #check if any games
    try:
        tree.xpath('//*[@class="nogames"]//text()')[0]
        print("no games today")
        urls['live'] = []
        urls['static'] = []
        return urls
    except:
        pass
        
    games = tree.xpath(
        '//*[@class="scoreboard-top no-tabs"]//table//thead//*[@class="date-time"]')
    games = [g.text_content() for g in games]
    print("games: ", games)
    boxscores = tree.xpath(
        '//*[@class="scoreboard-top no-tabs"]//*[@class="sb-actions"]//@href')
    boxscores = ['https://www.espn.com' +
                 b for b in boxscores if 'boxscore' in b]

    games = games[0:len(boxscores)]
    try:
        urls['live'] = [boxscores[i]
                        for i, s in enumerate(games) if is_live(s)]
    except Exception as ex:
        urls['live'] = []
        print("no live games")
        print(ex)
    try:
        urls['static'] = [boxscores[i]
                          for i, s in enumerate(games) if not is_live(s)]
    except Exception as ex:
        urls['static'] = []
        print("no static games")
        print(ex)
    print("success")
    #print("urls: ", urls)
    return urls


def get_team_info(tree, locale):
    team = {}
    team['city'] = tree.xpath('//*[@class="team ' + locale + '"]//*[@class="long-name"]//text()')[0]
    team['team'] = tree.xpath('//*[@class="team ' + locale + '"]//*[@class="short-name"]//text()')[0]
    team['abbrev'] = tree.xpath('//*[@class="team ' + locale + '"]//*[@class="abbrev"]//text()')[0]
    team['score'] = tree.xpath('//*[@class="team ' + locale + '"]//*[@class="score-container"]//text()')[0]

    status = tree.xpath('//*[@class="game-time status-detail"]')
    #TODO: check if game ended
    if 'Final' not in status:
        team['result'] = '-'
        #return team

    score = {}
    scores = tree.xpath('//*[@class="miniTable"]//tbody//*[@class="final-score"]//text()')
    score['away'] = int(str(scores[0]))
    score['home'] = int(str(scores[1]))

    if locale == "home": locale_other = "away"
    else: locale_other = "home"

    if score[locale] > score[locale_other]: team['result'] = "W"
    else: team['result'] = "L"

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
    try:
        counter = 0
        if int(log['pts']) > 10: counter += 1
        if int(log['reb']) > 10: counter += 1
        if int(log['ast']) > 10: counter += 1
        if int(log['stl']) > 10: counter += 1
        if int(log['blk']) > 10: counter += 1
        return counter
    except:
        return 0

def validate_log(log):
    for k in log:
        if log[k] in ('--', ''):
            log[k] = 0
    return log

def get_log(tree, r, locale, team, today):
    """takes gamelog table row and extracts each stat"""
    log = {}
    log['fullName'] = parse_name(r.xpath(
        './/*[@class="name"]')[0].text_content())
    log['position'] = r.xpath(
        './/*[@class="name"]//*[@class="position"]')[0].text_content()
    log['team'] = team[locale]['team']
    log['playerID'] = create_id(log['fullName'], team[locale])
    log['date'] = today
    try:
        log['time'] = tree.xpath('//*[@class="game-time status-detail"]//text()')[0]
    except:
        log['time'] = '-'
    log['location'] = team[locale]['city']
    log['result'] = team[locale]['result']
    if locale == "home": 
        log['opponent'] = team['away']['team']
    else: 
        log['opponent'] = team['home']['team']
    home_score = team['home']['abbrev'] + " " + team['home']['score']
    away_score = team['away']['abbrev'] + " " + team['away']['score']
    log['score'] = home_score + " | " + away_score
    log['min'] = r.xpath('.//*[@class="min"]')[0].text_content()
    #log['fg'] = r.xpath('.//*[@class="fg"]')[0].text_content()
    #log['3pt'] = r.xpath('.//*[@class="3pt"]')[0].text_content()
    ft = r.xpath('.//*[@class="ft"]')[0].text_content()
    log['ftm'] = ft.split('-')[0]
    log['fta'] = ft.split('-')[1]
    log['ftm/a'] = log['ftm'] + '/' + log['fta']
    log['ftpct'] = calc_pct(ft)
    fg = r.xpath('.//*[@class="fg"]')[0].text_content()
    log['fgm'] = fg.split('-')[0]
    log['fga'] = fg.split('-')[1]
    log['fgm/a'] = log['fgm'] + '/' + log['fga']
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
        
    log['imageURL'] = create_img_url(player_urls[log['fullName']])
    log['zScore'] = value_log(log)

    log = validate_log(log)

    return log


def update_player_urls(tree):
    names = tree.xpath('//*[@class="name"]//*[@class="abbr"]//text()')
    urls = tree.xpath('//*[@class="name"]//@href')
    
    for n in range(0, len(names)):
        player_urls[names[n]] = urls[n]

    #print("player_urls: ", player_urls)
    

def process_gamelogs(url, url_home):
    """takes gamelog url and parses gamelogs and adds them to data structures"""
    print("processing: ", url)
    tree = get_tree(url, 'html')

    try:
        if 'no box score' in tree.xpath('//*[@id="gamepackage-box-score"]//text()')[0].lower():
            print("no box score")
            return
    except:
        pass

    today = get_today(url_home)

    team_info = {}

    update_player_urls(tree)

    rows_home = tree.xpath('//*[@id="gamepackage-boxscore-module"]//*[@class="col column-two gamepackage-home-wrap"]//table//tr')
    rows_away = tree.xpath('//*[@id="gamepackage-boxscore-module"]//*[@class="col column-one gamepackage-away-wrap"]//table//tr')
    
    rows_home = [r for r in rows_home if is_stat_row(r.text_content())]
    rows_away = [r for r in rows_away if is_stat_row(r.text_content())]

    team_info['home'] = get_team_info(tree, "home")
    team_info['away'] = get_team_info(tree, "away")

    for r in rows_home:
        log = get_log(tree, r, "home", team_info, today)
        #each home log is created
        print("log: ", log)
        logs.append(log)

    for r in rows_away:
        log = get_log(tree, r, "away", team_info, today)
        #each away log is created
        print("log: ", log)
        logs.append(log)