from lxml import html
import requests
import pandas as pd
from time import sleep
import re
from collections import OrderedDict
import os
from datetime import datetime

domain = "https://www.espn.com"

#urls = tree.xpath('//*[@class="dropdown dropdown--md h-100 pageHeading__team-stats-dropdown"]//@data-url')

keywords = ['Team', 'Position', 'HT/WT', 'DOB', 'College', 'Draft Info', 'Status', 'Experience', 'Hometown']

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

    player['image_url'] = tree.xpath('//*[@class="Image__Wrapper aspect-ratio--auto"]//img//@src')[0]
    for i in range(0, len(info)-1):
        if info[i] in keywords:
            player[info[i]] = info[i+1]


    return player

#get team urls
team_url = "https://www.espn.com/nba/teams"
page = requests.get(team_url, timeout=3)
tree = html.fromstring(page.content)
team_urls = tree.xpath('//*[@class="AnchorLink"]/@href')
team_urls = [u for u in team_urls if 'roster' in u]

players = []
#get player urls
for t in team_urls:
    print("scraping: ", domain + t)
    teamName_path = t.split('/')[-1]
    page = requests.get(domain + t, timeout=3)
    tree = html.fromstring(page.content)

    #TODO: incorprate city and teamName into player bio data
    city = tree.xpath('//*[@class="flex flex-wrap"]//text()')[0]
    teamName = tree.xpath('//*[@class="flex flex-wrap"]//text()')[1]
    
    player_urls = tree.xpath('//*[@class="AnchorLink"]//@href')
    player_urls = list(OrderedDict.fromkeys(player_urls))
    
    #print("player urls: ", player_urls)
    
    for p in player_urls:
        player = get_player_info(p)
        print("player ", player)
        players.append(player)
        sleep(1.5)

    players = pd.DataFrame(players)

    try: os.mkdir('player_info/' + teamName_path)
    except: pass

    print("writing: ", teamName)
    players.to_csv("player_info/" + teamName_path + "/" + teamName_path + "-roster.csv", index=False)
    print(teamName, " written")

    sleep(4)
