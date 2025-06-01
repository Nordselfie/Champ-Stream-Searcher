import os
import json
import requests
import httpx
import asyncio

script_dir = os.path.dirname(os.path.abspath(__file__))
secretsFolder = os.path.join(script_dir, "secrets.json")

def loadsecrets():
    with open(secretsFolder, "r") as file:
        data = json.load(file)
        return data["apikey"], data["clientid"], data["clientsecret"], data["JSONURL"], data["JSONID"]

apikey, clientid, clientsecret, StreamerJSON, StreamerJSONID = loadsecrets()

riotheaders = {"X-Riot-Token": apikey}
ChampID_url = "https://ddragon.leagueoflegends.com/cdn/15.5.1/data/en_US/champion.json"

twitch_token_url = "https://id.twitch.tv/oauth2/token"
twitch_games_url = "https://api.twitch.tv/helix/games"
twitch_streams_url = "https://api.twitch.tv/helix/streams"
twitch_channel_url = "https://api.twitch.tv/helix/search/channels"

file_path = os.path.join(script_dir, "streamer_accounts.json")

tagsTable = {
    "leagueoflegends",
    "lol"
}

regionList = {
        "euw1",
        "eun1",
        "tr1",
        "ru",
        "na1",
        "br1",
        "la1",
        "la2",
        "kr",
        "jp1",
        # "europe",
        # "americas",
        # "asia"
}

# Create an async client for httpx - created once and reused
async_client = httpx.AsyncClient(headers=riotheaders)


def get_twitch_token():
    try:
        #Get twitch access token
        params = {
            "client_id": clientid,
            "client_secret": clientsecret,
            "grant_type": "client_credentials"
        }
        TwitchResponse = requests.post(twitch_token_url, params=params)
        TwitchResponse.raise_for_status()
        if TwitchResponse:
            return TwitchResponse.json()["access_token"]
    except Exception as e:
        print("Error twitch token", e)


def get_game_id(token):
    try:
        #get league of legends id on twitch
        TwitchGameIDHeaders = {"Client-ID": clientid, "Authorization": f"Bearer {token}"}
        TwitchGameIDparams = {"name": "League of Legends"}

        TwitchGameIDresponse = requests.get(twitch_games_url, headers=TwitchGameIDHeaders, params=TwitchGameIDparams)
        TwitchGameIDresponse.raise_for_status()

        TwitchIDdata = TwitchGameIDresponse.json()["data"]
        if TwitchIDdata:
            return TwitchIDdata[0]["id"]
    except Exception as e:
        print("Error twitch game id", e)


def get_account_region(region):
    mapping = {
        "euw1": "europe",
        "eun1": "europe",
        "tr1": "europe",
        "ru": "europe",
        "na1": "americas",
        "br1": "americas",
        "la1": "americas",
        "la2": "americas",
        "kr": "asia",
        "jp1": "asia",

        "europe": "europe",
        "americas": "americas",
        "asia": "asia"
    }
    return mapping.get(region, "europe")

def fix_region(region):
    region = region.lower()
    mapping = {
        "euw": "euw1",
        "eun": "eun1",
        "tr": "tr1",
        "ru": "ru",
        "na": "na1",
        "br": "br1",
        "la": "la1",
        "la2": "la2",
        "kr": "kr",
        "jp": "jp1",

        "euw1": "euw1",
        "eun1": "eun1",
        "tr1": "tr1",
        "ru": "ru",
        "na1": "na1",
        "br1": "br1",
        "la1": "la1",
        "la2": "la2",
        "kr": "kr",
        "jp1": "jp1",
    }

    return mapping.get(region, "none")

def get_champion(RequestedData:str, InputData):
    #get champion id with a name
    response = requests.get(ChampID_url)
    if response.ok:
        champion_data = response.json()["data"]
        if RequestedData == "ID":
            for champname, champinfo in champion_data.items():
                if champname.lower() == InputData.lower():
                    return int(champinfo["key"])
        else:
            for champname, champinfo in champion_data.items():
                if int(champinfo["key"]) == InputData:
                    return champname

def find_channel(streamername, token):
    headers = {'Client-ID': clientid, 'Authorization': f'Bearer {token}'}
    params = {"query": streamername}
    response = requests.get(twitch_channel_url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json().get("data", [])

    for channel in data:
        if channel["broadcaster_login"] == streamername:
            return channel
    return "none"


def get_streams(token, gameid):
    headers = {'Client-ID': clientid, 'Authorization': f'Bearer {token}'}
    params = {"game_id": gameid, "first": 100, "type": "live"} #Limit is 100, only get live streams.
    response = requests.get(twitch_streams_url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()["data"]

    results = []
    if data:
        for stream in data:
            streamername = stream["user_name"]
            title = stream["title"]
            TwitchUserid = stream["user_id"]
            results.append((streamername, title, TwitchUserid))
    return results

# Asynchronous version of riot_api_request using httpx async_client
async def async_riot_api_request(url):
    # Use the globally defined async_client
    response = await async_client.get(url)
    response.raise_for_status()
    data = response.json()
    if data:
        return data
    return None # Return None if no data

# Asynchronous version of get_puuid
async def async_get_puuid(riot_id, routingregion):
    account_region = get_account_region(routingregion)
    try:
        #splitting the name and tagline
        gamename, tagline = riot_id.split("#")
        gamename = gamename.strip()
        tagline = tagline.strip()
    except ValueError:
        # Handle cases where riot_id doesn't contain '#'
        # print(f"Invalid Riot ID format: {riot_id}") # Optional: log errors
        return None


    url = f"https://{account_region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gamename}/{tagline}"
    try:
        data = await async_riot_api_request(url)
        if data:
            puuid = data.get("puuid")
            return puuid
        return None
    except Exception as e:
        # print(f"Error getting PUUID for {riot_id}: {e}") # Optional: log errors
        return None

# Asynchronous version of get_player_champ
async def async_get_player_champ(puuid, playerregion:str):
    Fixedplayerregion = fix_region(playerregion.lower())
    if Fixedplayerregion == "none":
        # print(f"Invalid region for PUUID {puuid}: {playerregion}") # Optional: log errors
        return None # Handle invalid region early

    url = f"https://{Fixedplayerregion}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}"
    try:
        data = await async_riot_api_request(url)
        if data:
            participants = data.get("participants", [])
            for player in participants:
                if player.get("puuid") == puuid:
                    return player.get("championId")
            return None # PUUID not found in game participants
        return None # No active game data found
    except Exception as e:
        # print(f"Error getting player champ for PUUID {puuid}: {e}") # Optional: log errors
        return None

def GetStreamerJson():
    url = f"https://jsonblob.com/api/jsonBlob/{StreamerJSONID}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print("Failed to get streamers json file, error code: " + str(response.status_code))
            return None
    except requests.RequestException as e:
        print("Request failed:", e)
        return None
    


def add_streamer_mapping(twitch_name, lol_name, region):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    twitch_key = twitch_name.lower()
    account_entry = {"name": lol_name, "region": region.upper()}

    if twitch_key not in data:
        data[twitch_key] = {
            "accounts": [account_entry]
        }
    else:
        accounts = data[twitch_key].get("accounts", [])
        # Avoid duplicates
        if not any(acc["name"] == lol_name and acc["region"] == region.upper() for acc in accounts):
            accounts.append(account_entry)
        data[twitch_key]["accounts"] = accounts

    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Mapped {twitch_name} to {lol_name} ({region})")
    except PermissionError:
        print(f"Permission denied while writing to {file_path}")