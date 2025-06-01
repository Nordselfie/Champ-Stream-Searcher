import tkinter
from tkinter import scrolledtext
import tkinter.font as tkfont
import Main as Functions
import os
import json
import threading
import asyncio

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "streamer_accounts.json")

RIOT_API_SEMAPHORE = asyncio.Semaphore(5)
REQUEST_DELAY = 0.1 # seconds


def log(text):
    output.configure(state='normal')
    output.insert(tkinter.END, text + '\n')
    output.configure(state='disabled')
    output.see(tkinter.END)

def draw_gradient(canvas, width, height, color1, color2):
    r1, g1, b1 = canvas.winfo_rgb(color1)
    r2, g2, b2 = canvas.winfo_rgb(color2)

    r_ratio = (r2 - r1) / height
    g_ratio = (g2 - g1) / height # Corrected: should be g2 - g1
    b_ratio = (b2 - b1) / height

    for i in range(height):
        nr = int(r1 + (r_ratio * i))
        ng = int(g1 + (g_ratio * i))
        nb = int(b1 + (b_ratio * i))
        hex_color = f"#{nr >> 8:02x}{ng >> 8:02x}{nb >> 8:02x}"
        canvas.create_line(0, i, width, i, fill=hex_color)

def on_enter(e):
    e.widget['background'] = '#555555'

def on_leave(e):
    e.widget['background'] = '#222222'


root = tkinter.Tk()
root.geometry("800x600")
root.configure(background="#000000")
root.title("Champion Streams Finder")
root.resizable(False, False)
# root.overrideredirect(True)

width, height = 800, 600
canvas = tkinter.Canvas(root, width=width, height=height, bd=0, highlightthickness=0)
canvas.pack(fill="both", expand=True)
canvas.pack()


draw_gradient(canvas, width, height, "#000000", "#2c2c2c")

canvas.create_text(
    width // 2, 60,
    text="Insert Champion Name",
    fill="#FFFFFF",
    font=("Helvetica", 30, "bold")
)

champInsertion = tkinter.Entry(
    root,
    width=20,
    bg="#000000",
    fg="#FFFFFF",
    font=("Helvetica", 20, "bold"),
    justify="center",
    bd=0,
    highlightthickness=0,
    relief="flat"
)
canvas.create_window(width // 2, 120, window=champInsertion)




output = scrolledtext.ScrolledText(
    root,
    wrap=tkinter.WORD,
    width=80,
    height=10,
    state="disabled",
    bg="#000000",
    fg="#ffffff",
    relief="flat",
    font=tkfont.Font(family="Helvetica", weight="bold")
)

output.config(padx=10, pady=10)
canvas.create_window(width // 2, 320, window=output, anchor="center")


text = canvas.create_text(
    width // 2, 450,
    text="-Manual Streamer Mapping-",
    fill="#FFFFFF",
    font=("Helvetica", 15, "bold")
)

y_pos = 490
twitchNameText = canvas.create_text(width // 2 - 250, y_pos, text="Twitch Name", fill="white", font=("Helvetica", 12, "bold"), anchor="center")
riotidText = canvas.create_text(width // 2, y_pos, text="Riot ID", fill="white", font=("Helvetica", 12, "bold"))
regionText = canvas.create_text(width // 2 + 250, y_pos, text="Region", fill="white", font=("Helvetica", 12, "bold"), anchor="center")

# canvas.itemconfig(twitchNameText, justify="center")
# canvas.itemconfig(riotidText, justify="center")
# canvas.itemconfig(regionText, justify="center")

TwitchName = tkinter.Entry(
    root,
    width=20,
    bg="#000000",
    fg="#FFFFFF",
    font=("Helvetica", 15, "bold"),
    justify="center",
    bd=0,
    highlightthickness=0,
    relief="flat"
)
canvas.create_window(width // 2 - 250, y_pos + 40, window=TwitchName)

RiotId = tkinter.Entry(
    root,
    width=20,
    bg="#000000",
    fg="#FFFFFF",
    font=("Helvetica", 15, "bold"),
    justify="center",
    bd=0,
    highlightthickness=0,
    relief="flat"
)
canvas.create_window(width // 2, y_pos + 40, window=RiotId)

Region = tkinter.Entry(
    root,
    width=20,
    bg="#000000",
    fg="#FFFFFF",
    font=("Helvetica", 15, "bold"),
    justify="center",
    bd=0,
    highlightthickness=0,
    relief="flat"
)
canvas.create_window(width // 2 + 250, y_pos + 40, window=Region)




#_____________________________LOGIC_____________________________\
data = Functions.GetStreamerJson()
TwitchToken = Functions.get_twitch_token()
gameid = Functions.get_game_id(TwitchToken)
# log(f"Twitch Token: {TwitchToken}")
# log(f"GameID: {gameid}")

# Helper async function to process a single streamer account with rate limiting
async def process_streamer_account(streamer_info, target_champion_id):
    streamername = streamer_info["streamername"]
    summonername = streamer_info["summonername"]
    region = streamer_info["region"]

    puuid = None
    # Acquire semaphore before making the API call
    async with RIOT_API_SEMAPHORE:
        # Add a small delay to space out requests
        await asyncio.sleep(REQUEST_DELAY)
        puuid = await Functions.async_get_puuid(summonername, region)

    if puuid:
        champion_id = None
        # Acquire semaphore before making the API call
        async with RIOT_API_SEMAPHORE:
            # Add a small delay to space out requests
            await asyncio.sleep(REQUEST_DELAY)
            champion_id = await Functions.async_get_player_champ(puuid, region)

        if champion_id is not None:
            try:
                ChampionInGameName = Functions.get_champion("ChampionName", champion_id)
            except Exception as error:
                log(f"Error converting champion key to name: {error}")
                ChampionInGameName = str(champion_id)

            if champion_id == target_champion_id:
                log(f"Streamer: {streamername} ({summonername} - {region}) is currently playing: {ChampionInGameName}")
                return True # Indicate that a streamer was found playing the champion

    return False # Indicate that this streamer was not found or not playing the champion


# Make onclick_thread an async function
async def onclick_thread_async():
    ChampionText = champInsertion.get().strip()
    if not ChampionText:
        log("Please insert a champion name.")
        return

    try:
        championId = Functions.get_champion("ID", ChampionText)
        if championId is None:
            log("Champion name is invalid.")
            return
        log("Champion key: " + str(championId))
    except Exception as error:
        log("Error with getting champion key. Error: " + str(error))
        return

    found_any = False
    processing_tasks = []

    # Prepare tasks for concurrent execution using the helper function
    for player, info in data.items():
        accounts = info.get("accounts", [])
        for account in accounts:
            streamer_info = {"streamername": player, "summonername": account.get("name"), "region": account.get("region")}
            if streamer_info["summonername"] and streamer_info["region"]:
                processing_tasks.append(process_streamer_account(streamer_info, championId))

    # Run processing tasks concurrently, limited by the semaphore
    results = await asyncio.gather(*processing_tasks)

    # Check if any task returned True (meaning a streamer was found playing the champion)
    if any(results):
        found_any = True

    if not found_any:
        log(f"No streamers are currently playing {ChampionText}.")


# Modify onclick to run the async function
def onclick():
    # Use asyncio.run to run the top-level async function in a new event loop
    threading.Thread(target=lambda: asyncio.run(onclick_thread_async()), daemon=True).start()


# Modify onclickMap_thread to be async and use the semaphore
async def onclickMap_thread_async():
    twitchname = TwitchName.get().strip()
    riotname = RiotId.get().strip()
    region = Region.get().strip().lower()

    FoundTwitchProof = False
    FoundRiotProof = False

    # Twitch check (synchronous)
    ChannelData = Functions.find_channel(twitchname, TwitchToken)
    if ChannelData != "none":
        channelLogin = ChannelData["broadcaster_login"]
        # Check if 'tags' key exists and is not None before iterating
        if 'tags' in ChannelData and ChannelData['tags'] is not None:
            for tag in ChannelData["tags"]:
                if tag.lower() in Functions.tagsTable:
                    FoundTwitchProof = True
                    log(f"Found Proof for streamer: {channelLogin} via tags")

        if ChannelData.get("game_id") == gameid: # Use .get() for safety
            FoundTwitchProof = True
            log(f"Found proof for streamer {channelLogin} via live/recent games played")

    newRegion = Functions.fix_region(region)
    if newRegion == "none":
        log("Region invalid, please insert proper region")
        return

    log(f"Changed region from {region} to {newRegion}")
    routingregion = Functions.get_account_region(newRegion)

    # Riot check (asynchronous with semaphore)
    playerpuuid = None
    # Acquire semaphore before making the API call
    async with RIOT_API_SEMAPHORE:
        # Add a small delay to space out requests
        await asyncio.sleep(REQUEST_DELAY)
        playerpuuid = await Functions.async_get_puuid(riotname, routingregion)


    if playerpuuid:
        FoundRiotProof = True
        log(f"Found Proof for Riot account: {riotname}")

    if FoundTwitchProof and FoundRiotProof:
        Functions.add_streamer_mapping(twitchname, riotname, newRegion)
        log(f"Streamer successfully mapped twitch name: {twitchname}, riot name: {riotname}, region: {newRegion}")
    else:
        log("Could not verify both Twitch and Riot accounts. Mapping not added.")


# Modify onclickMap to run the async function
def onclickMap():
    # Use asyncio.run to run the top-level async function in a new event loop
    threading.Thread(target=lambda: asyncio.run(onclickMap_thread_async()), daemon=True).start()


#Delay the creation of the buttons so we connect it with the functions.
button = tkinter.Button(
    root,
    text="Check Streamers",
    bg="#222222",
    fg="#FFFFFF",
    activebackground="#444444",
    activeforeground="#FFFFFF",
    relief="flat",
    font=("Helvetica", 14, "bold"),
    bd=0,
    highlightthickness=0,
    padx=10,
    pady=5,
    command=onclick # This now calls the wrapper that runs the async function
)

button.bind("<Enter>", on_enter)
button.bind("<Leave>", on_leave)

canvas.create_window(width // 2, 180, window=button)


mapbutton = tkinter.Button(
    root,
    text="Map Streamer",
    bg="#222222",
    fg="#FFFFFF",
    activebackground="#444444",
    activeforeground="#FFFFFF",
    relief="flat",
    font=("Helvetica", 8, "bold"),
    bd=0,
    highlightthickness=0,
    padx=10,
    pady=5,
    command=onclickMap # This still calls the threaded function
)

mapbutton.bind("<Enter>", on_enter)
mapbutton.bind("<Leave>", on_leave)

canvas.create_window(width // 2, 570, window=mapbutton)


root.mainloop()