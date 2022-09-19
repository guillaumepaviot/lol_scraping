import requests
import pandas as pd
import datetime
import time as t
from google.oauth2 import service_account
from googleapiclient.discovery import build


# For any URL, return the JSON
def return_json(URL, session):
    while True:
        response = session.get(URL)
        try:
            # Check for 404 error and quit if received
            if response.json()['status']['status_code'] == 404:
                return "error - status code 404"
            # Check for 429 (too many requests made), sleep if received
            elif response.json()['status']['status_code'] == 429:
                t.sleep(10)
                continue
            else:
                return "error - unknown reason"
        except:
            break
    return response.json()

# Provide the match-id & region, receive the json of match timeline (1 minute interval of match data)
def get_matchTimeline(matchId, region, key, session):
    URL = 'https://' + region + '.api.riotgames.com/lol/match/v5/timelines/by-match/' + str(
        matchId) + '/?api_key=' + key
    json = return_json(URL, session)
    return json


# Provide the match-id & region, receive the match information (game length, participants etc..)
def get_gameInfo(matchId, region, key, session):
    URL = 'https://' + region + '.api.riotgames.com/lol/match/v5/matches/' + str(matchId) + '/?api_key=' + key
    json = return_json(URL, session)
    return json

#Provide the match and player puuid and return the player's stats
def getPlayerStats(match, player_puuid):
    players = match["info"]["participants"]
    for player in players:
        if player["puuid"] == player_puuid :
            pro = player
    selected_key = ['summonerName', 'puuid', 'championName', 'championId', 'kills', 'deaths', 'assists', 'role', 'item0', 'item1', 'item2', 'item3', 'item4', 'item5', 'item6', 'summoner1Id', 'summoner2Id', 'teamPosition', 'win']
    stats = { key:value for (key,value) in pro.items() if key in selected_key}
    runes = pro['perks']['styles']
    stats['primaryStylePerk'] = runes[0]['style']
    primary_runes = runes[0]['selections']
    for idx, item in enumerate(primary_runes):
        stats['primaryStylePerks' + str(idx+1)] = item['perk']
    stats['secondaryStylePerk'] = runes[1]['style']
    secondary_runes = runes[1]['selections']
    for idx, item in enumerate(secondary_runes):
        stats['secondaryStylePerks' + str(idx+1)] = item['perk']
    return stats

#Provide the match and a role and return the opponent's champion and summoners
def getOpponentStats(match, role, player_puuid):
    players = match["info"]["participants"]
    for player in players:
        if player["teamPosition"] == role and player['puuid'] != player_puuid:
            pro = player
    selected_key = ['championName', 'championId', 'kills', 'deaths', 'assists', 'summoner1Id', 'summoner2Id',]
    stats = { key:value for (key,value) in pro.items() if key in selected_key}
    runes = pro['perks']['styles']
    stats['primaryStylePerkKeystone'] = runes[0]['selections'][0]['perk']
    stats['secondaryStylePerk'] = runes[1]['style']
    return stats

def main():
    players_data = pd.read_csv('players.csv')
    session = requests.Session()

    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # The ID and range of a sample spreadsheet.
    SAMPLE_SPREADSHEET_ID = ''
    range_ = 'A10182:AL10283'
    SERVICE_ACCOUNT_FILE = ''

    credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    service = build('sheets', 'v4', credentials=credentials)

    for index, row in players_data.iterrows():
        start_time = t.time()
        print("Player found : %s" %(row['Name']))
        all_player_data_dict = []
        player_puuid = row['Puuid']
        matches_url = 'https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/' + str(player_puuid) + '/ids?start=0&count=100&' + 'api_key='
        matches = return_json(matches_url, session)
        print("Found %s games" %(len(matches)))
        for match_id in matches :
            try : 
                match = get_gameInfo(match_id,'europe' ,'api_key', session)
                player_stats = getPlayerStats(match, player_puuid)
                opponent_stats = getOpponentStats(match, player_stats['teamPosition'], player_puuid)
                all_player_data_dict.append(
                    {
                        'Player': row['Name'],
                        'Team': row['Team'],
                        'Account': player_stats['summonerName'],
                        'Champion': player_stats['championName'],
                        'ChampionId': player_stats['championId'],
                        'Team Role': row['Role'],
                        'Game Role': player_stats['teamPosition'],
                        'Summoner 1': player_stats['summoner1Id'],
                        'Summoner 2': player_stats['summoner2Id'],
                        'Win': player_stats['win'],
                        'Kills': player_stats['kills'],
                        'Deaths': player_stats['deaths'],
                        'Assists': player_stats['assists'],
                        'Item 1': player_stats['item0'],
                        'Item 2': player_stats['item1'],
                        'Item 3': player_stats['item2'],
                        'Item 4': player_stats['item3'],
                        'Item 5': player_stats['item4'],
                        'Item 6': player_stats['item5'],
                        'Primary Perk Style': player_stats['primaryStylePerk'],
                        'Primary Perk Keystone': player_stats['primaryStylePerks1'],
                        'Primary Perk 2': player_stats['primaryStylePerks2'],
                        'Primary Perk 3': player_stats['primaryStylePerks3'],
                        'Primary Perk 4': player_stats['primaryStylePerks4'],
                        'Secondary Perk Style': player_stats['secondaryStylePerk'],
                        'Secondary Perk 1': player_stats['secondaryStylePerks1'],
                        'Secondary Perk 2': player_stats['secondaryStylePerks2'],
                        'Opponent Champion': opponent_stats['championName'],
                        'Opponent ChampionId': opponent_stats['championId'],
                        'Opponent Kills': opponent_stats['kills'],
                        'Opponent Deaths': opponent_stats['deaths'],
                        'Opponent Assists': opponent_stats['assists'],
                        'Opponent Summoner 1': opponent_stats['summoner1Id'],
                        'Opponent Summoner 2': opponent_stats['summoner2Id'],
                        'Opponent Primary Perk Keystone': opponent_stats['primaryStylePerkKeystone'],
                        'Opponent Secondary Perk Style': opponent_stats['secondaryStylePerk'],
                        'Duration': str(datetime.timedelta(milliseconds=round(match['info']['gameDuration']))),
                        'Game Started': str(datetime.datetime.fromtimestamp(round(match['info']['gameStartTimestamp']/1000))),
                    }
                )
            except:
                pass
        all_player_data = pd.DataFrame(all_player_data_dict)
        range_ = 'A1:AL101'
        request = service.spreadsheets().values().append(
            spreadsheetId=SAMPLE_SPREADSHEET_ID, 
            range=range_, 
            valueInputOption='USER_ENTERED', 
            insertDataOption='INSERT_ROWS', 
            body=dict(
                    majorDimension='ROWS',
                    values=all_player_data.T.reset_index().T.values.tolist()
                    )
            )
        response = request.execute()
        print("Sheet updated succesfully")
        print("--- %s seconds ---" % (t.time() - start_time))

if __name__ == "__main__":
    main()