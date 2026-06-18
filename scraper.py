import os
import csv 
from dotenv import load_dotenv
import requests
import sys
import json 
import gspread

import gspread

class JSONUpdater:
    def __init__(self):
        self.path = "dmg_total.json"
    
    def status(self):
        with open(self.path, 'r') as file:
            data = json.load(file)

            return f"Total Dmg Tracker Across {data['num_games']} games\n Anthotron: {data['Anthotron']}\n Jeans: {data['iLuvNewjeans']}\n Zeegy: {data['Zeegy']}"
    def read_file(self):
        with open(self.path, 'r') as file:
            data = json.load(file)
            # print(data)
            return (data)
        
    def update_json(self, zeegy_dmg, anthotron_dmg, jeans_dmg):
        data = self.read_file()

        data['Anthotron'] += anthotron_dmg
        data['iLuvNewjeans'] += jeans_dmg
        data['Zeegy'] += zeegy_dmg
        data['num_games'] += 1

        with open(self.path, 'w', encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def call(self, zeegy_dmg, anthotron_dmg, jeans_dmg):
        self.update_json(zeegy_dmg, anthotron_dmg, jeans_dmg)
        data = self.read_file()

        return f"Total Dmg Tracker Across {data['num_games']} games\n Anthotron: {data['Anthotron']}\n Jeans: {data['iLuvNewjeans']}\n Zeegy: {data['Zeegy']}"
class SheetWriter:
    def __init__(self, sheet_name="Arena Tracker"):
        creds = json.loads(os.environ["GSPREAD_CREDENTIALS"])
        authorized_user = json.loads(os.environ["GSPREAD_AUTHORIZED_USER"])
        self.gc, _ = gspread.oauth_from_dict(
            credentials=creds,
            authorized_user_info=authorized_user,
        )
        self.players = ["Anthotron", "iLuvNewjeans", "Zeegy"]   # column order
        self.players_second = ['']
        try:
            self.sh = self.gc.open(sheet_name)          # open if it exists
        except gspread.SpreadsheetNotFound:
            self.sh = self.gc.create(sheet_name)        # otherwise create it (you own it)
            self._write_header()

        self.ws = self.sh.sheet1
    def _write_header(self):
        header = ["Game", ""] + self.players
        self.sh.sheet1.update([header], "A1")           # values first, range second (gspread 6.x)

    def next_game_number(self):
        labels = self.ws.col_values(2)                  # column B: "", "Champion", "Damage", ...
        return labels.count("Champion") + 1

    def add_game(self, game_num, results):
        # results = {"Anthotron": ("Anivia", 28646), ...}  -> (champion, damage)
        champ_row = [game_num, "Champion"] + [results.get(p, ("", ""))[0] for p in self.players]
        dmg_row   = ["",       "Damage"]   + [results.get(p, ("", ""))[1] for p in self.players]
        self.ws.append_rows([champ_row, dmg_row], value_input_option="USER_ENTERED")

class RiotScraper:
    def __init__(self, api_key=None, region="americas", cache_path="puuid.csv"):
        sys.stdout.reconfigure(encoding='utf-8')
        load_dotenv()
        self.API_KEY = os.getenv("API_KEY")
        self.region = region
        self.cache_path = cache_path

    #csv stuff
    def insert_into_csv(self, GameName, puuid, tagLine):
        #Writes into puuid.csv 
        with open('puuid.csv', 'a', newline='') as file:
            csv.writer(file).writerow([GameName + '#' + tagLine, puuid])

    def name_in_csv(self, name, path='puuid.csv'):
        #Checks if the name is in the csv
        with open(path, newline='') as f:
            return any(row and row[0].lower() == name.lower() for row in csv.reader(f))

    def get_from_csv(self, name, path='puuid.csv'):
        #Gets the puuid from csv
        with open(path, newline='') as f:
            for row in csv.reader(f):
                if row and row[0].lower() == name.lower():
                    return row  # [GameName#tag, puuid]
        return None

    def resolve_puuid(self, player_name, tagline):
        #Puts puuid into csv if not in
        # always returns puuid of player
        concat = player_name + '#' + tagline
        if not self.name_in_csv(concat):
            puuid = self.get_puuid(player_name, tagline)
            self.insert_into_csv(player_name, puuid, tagline)
            return puuid
        return self.get_from_csv(concat)[1].strip()

    # Riot API
    def get_puuid(self, player_name, tagline):
        #Gets puuid
        url = (f"https://{self.region}.api.riotgames.com"
               f"/riot/account/v1/accounts/by-riot-id/{player_name}/{tagline}"
               f"?api_key={self.API_KEY}")
        return requests.get(url).json()['puuid']

    def get_match_by_puuid(self, puuid):
        # returns most recent Arena match id, or -1
        url = (f"https://{self.region}.api.riotgames.com"
               f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
               f"?start=0&count=20&api_key={self.API_KEY}")
        match_ids = requests.get(url).json()
        for match_id in match_ids:
            if self.check_if_arena(match_id):
                return match_id
        return -1

    def check_if_arena(self, game_id):
        #Checks if the game is Arena, CHERRY = Arena
        return self._get_match_info(game_id)['gameMode'] == 'CHERRY'

    def _get_match_info(self, match_id):
        #Gets match information from API, there's so much stuff in there idk
        url = (f"https://{self.region}.api.riotgames.com"
               f"/lol/match/v5/matches/{match_id}?api_key={self.API_KEY}")
        return requests.get(url).json()['info']

    # 
    def last_recorded_match(self, path='prev_game.json'):
        try:
            with open(path) as f:
                return json.load(f).get('last_match')
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def mark_recorded(self, match_id, path='prev_game.json'):
        try:
            with open(path) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        data['last_match'] = match_id
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    
    def scrape_shared_game(self, players):
        """
        players: [[riot_game_name, tagline, sheet_label], ...]
        Returns (results, match_id):
          results = {label: (champion, damage)}  -> a new game to record
          (None, match_id)  -> latest Arena game already recorded
          (None, None)      -> no Arena game found
        """
        primary_name, primary_tag, _ = players[0]
        puuid = self.resolve_puuid(primary_name, primary_tag)

        match_id = self.get_match_by_puuid(puuid)
        if match_id == -1:
            return None, None
        if match_id == self.last_recorded_match():
            return None, match_id

        parts = self._get_match_info(match_id)['participants']
        results = {}
        for game_name, _tag, label in players:
            for p in parts:
                if p['riotIdGameName'].lower() == game_name.lower():
                    results[label] = (p['championName'],
                                      p['totalDamageDealtToChampions'])
                    break
        return results, match_id
    
if __name__ == '__main__':
    if 1:
        scraper = RiotScraper()
        writer = SheetWriter(sheet_name="Arena Tracker")
        reader = JSONUpdater()
        
        print(reader.call(1000, 2000, 3000))
     

        # writer.add_game(1, {
        #     "Anthotron":    ("Another Champ -1",  5),
        #     "iLuvNewjeans": ("Another Champ -2", 11),
        #     "Zeegy":        ("Another Champ -3",   22),
        # })
        # print("wrote game 1 — check your Drive for 'Arena Tracker'")
   
        # arena_players = [['Zeegyboogydoog', 'NA1'], ['Anthotron713', 'NA1'], ['iLuvNewjeans', '6884']]
        # for player in arena_players:
        #     val, val2 = scraper.scrape(player[0], player[1])
        #     print(val, val2)