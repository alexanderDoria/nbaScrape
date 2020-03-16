# nbaScrape

## overview
scrapes NBA stats from ESPN, used for [Fantasy Basketball WZRD](https://github.com/bilalsattar24/fantasyBasketballWizard).

## ESPN
  - scrapes NBA historical stats given defined date ranges, renders JS using requests-html (espn/espn_gamelogs_historical.py)
  - scrapes NBA live stats on espn.com/nba/scoreboard (espn/espn_gamelogs_live_local.py)
  - scrapes NBA live stats on espn.com/nba/schedule, more server friendly since it uses common libraries (requests, lxml) and doesn't render JS (espn/espn_gamelogs_live_server.py)
  - scrapes NBA player info (nba/espn_player_info.py)
  - determine statistical value of a player (espn/stats_utils.py)
  - **scraping modules can be found in espn/scrape_utils.py**
  - *no login required*

### summary

fetches gamelog from NBA on ESPN and returns gamelog dictionary, output can be written to csv or uploaded to a server 

![espn](https://i.imgur.com/YAkYE1H.png)

## Yahoo
  - scrapes NBA season stats (statScraper9cat.py)
  - login to fantasy required
