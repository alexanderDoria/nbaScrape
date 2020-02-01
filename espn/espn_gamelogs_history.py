from lxml import html
import requests
import pandas as pd
from time import sleep
import re
from collections import OrderedDict
import os
from datetime import datetime
import sys
from random import randint

domain = "https://www.espn.com"

#urls = tree.xpath('//*[@class="dropdown dropdown--md h-100 pageHeading__team-stats-dropdown"]//@data-url')

keywords = ['Team', 'Position', 'HT/WT', 'DOB', 'College', 'Draft Info', 'Status', 'Experience', 'Hometown']
weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
months = ['august', 'september', 'october', 'november', 'december', 'january', 'february', 'march', 'april']

def get_tree(url):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    return tree

def get_player_info(url):
    player = OrderedDict()

    player["url"] = url

    #get bio
    tree = get_tree(url.replace('/_/id/', '/bio/_/id/'))
    info = tree.xpath('//*[@class="Wrapper Card__Content"]//text()')

    player['First Name'] = tree.xpath('//*[@class="truncate min-w-0 fw-light"]//text()')[0]
    player['Last Name'] = tree.xpath('//*[@class="PlayerHeader__Name flex flex-column ttu fw-bold pr4 h2"]//*[@class="truncate min-w-0"]//text()')[0]

    for i in range(0, len(info)-1):
        if info[i] in keywords:
            player[info[i]] = info[i+1]

    return player

def get_season_info(tree):
    season = []
    this = 0
    dropdowns = tree.xpath('//*[@class="inline-flex filters"]//*[@class="dropdown"]//select')
    for d in range(0, len(dropdowns)):
        if '20' in dropdowns[d].value:
            this = int(dropdowns[d].value)
            season['this'] = this
            season['count'] = len(dropdowns[d].value_options)
            break

    if not this:
        year = datetime.today().year
        month = datetime.today().month
        if month <= 12 and month >= 9: season['season'] = year + 1
        else: season['season'] = year

    return season

def get_season_now():
    year = datetime.today().year
    month = datetime.today().month
    if month <= 12 and month >= 9: return year + 1
    else: return year

def get_season_count(tree):
    dropdowns = tree.xpath('//*[@class="inline-flex filters"]//*[@class="dropdown"]//select')
    for d in range(0, len(dropdowns)):
        if '20' in dropdowns[d].value:
            return len(dropdowns[d].value_options)

    return 1

def get_season_on_page(tree):
    dropdowns = tree.xpath('//*[@class="inline-flex filters"]//*[@class="dropdown"]//select')
    for d in range(0, len(dropdowns)):
        if '20' in dropdowns[d].value:
            return int(dropdowns[d].value)

    return get_season_now()


def process_date(d, season):
    date = d.split()[1]
    month = date.split('/')[0]
    day = date.split('/')[1]

    if month <= '12' and month >= '9':
        season -= 1

    return str(season) + '-' + month.zfill(2) + '-' + day.zfill(2)

def get_log(game, season, url):
    #print("game: ", game)
    log = OrderedDict()
    log['url'] = url
    log['season'] = str(season - 1) + '-' + str(season)
    log['date'] = process_date(game[0], season)
    #TODO: make home/away
    log['location'] = game[1]
    log['opponent'] = game[2]
    log['result'] = game[3]
    log['score'] = game[4]
    log['min'] = game[5]
    log['fg'] = game[6]
    log['fg%'] = game[7]
    log['3pt'] = game[8]
    log['3p%'] = game[9]
    log['ft'] = game[10]
    log['ft%'] = game[11]
    log['reb'] = game[12]
    log['ast'] = game[13]
    log['blk'] = game[14]
    log['stl'] = game[15]
    log['pf'] = game[16]
    log['to'] = game[17]
    log['pts'] = game[18]
    return log

def get_player_stats(url):

    #TODO: check if stats exist

    #get gamelogs
    url = url.replace('/_/id/', '/gamelog/_/id/')
    url = url.split('/')
    url = url[0:len(url)-1]
    url = '/'.join(url)
    url += '/type/nba/year/' + str(get_season_now())

    tree = get_tree(url)
    num_seasons = get_season_count(get_tree(url))
    season = get_season_on_page(tree)

    logs = []

    for s in range(0, num_seasons):
        
        print("url: ", url)
        tree = get_tree(url)
        
        info = tree.xpath('//*[@class="gamelog br-4 pa4 mb3 bg-clr-white"]//text()')

        reg = [i for i, s in enumerate(info) if 'Regular Season' in s]
        start = reg[0]
        #find stats using regular season end label 
        if len(reg) > 1: end = reg[1]
        else:
            try:
                end = [i for i, s in enumerate(info) if 'Preseason' in s][0]
            except:
                end = len(info)

        info = info[start:end]
        #print('info: ', info)

        #parse game log rows
        games = [i for i, s in enumerate(info) if '/' in s]
        
        for g in range(0, len(games)):
            game = info[games[g]:games[g]+19]
            #print("game: ", game)
            log = get_log(game, season, url)
            if log:
                logs.append(log)

        prev_season = season - 1
        url = url.replace('/' + str(season), '/' + str(prev_season))
        season = prev_season

        print("sleeping...")
        sleep(randint(2,5))
        print("sleep done")

    return logs

def stats(url, teamName_path='adhoc'):
    player_name = url.split('/')[-1]
    try:
        print("player url: ", url)
        print("fetching: ", player_name)
        player_logs = get_player_stats(url)
        #print("player ", player)
        print("fetching done")

        player_logs = pd.DataFrame(player_logs)

        try: os.mkdir('player_info/' + teamName_path)
        except: pass

        print("writing: ", player_name)
        player_logs.to_csv("player_info/" + teamName_path + "/" + player_name + "-logs.csv", index=False)
        print("writing done")

    except Exception as ex:
        print("error: ", player_name, " -- ", url)
        print(ex)
    

#check for adhoc run
if len(sys.argv) > 1:
    stats(sys.argv[1])
    exit()

#get team urls
team_url = "https://www.espn.com/nba/teams"
page = requests.get(team_url, timeout=3)
tree = html.fromstring(page.content)
team_urls = tree.xpath('//*[@class="AnchorLink"]/@href')
team_urls = [u for u in team_urls if 'roster' in u]

#get player urls
for t in team_urls:
    print("team url: ", domain + t)
    teamName_path = t.split('/')[-1]
    page = requests.get(domain + t, timeout=3)
    tree = html.fromstring(page.content)

    #TODO: incorprate city and teamName into player bio data
    city = tree.xpath('//*[@class="flex flex-wrap"]//text()')[0]
    teamName = tree.xpath('//*[@class="flex flex-wrap"]//text()')[1]
    
    player_urls = tree.xpath('//*[@class="AnchorLink"]//@href')
    player_urls = list(OrderedDict.fromkeys(player_urls))
    
    #print("player urls: ", player_urls)
    
    player_logs = []
    for p in player_urls:
        stats(p, teamName_path)
        
        print("sleeping...")
        sleep(randint(3,6))
        print("sleep done")

