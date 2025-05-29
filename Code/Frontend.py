import tkinter
from tkinter import scrolledtext
import tkinter.font as tkfont
import Main as Functions
import os
import json
import threading

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "streamer_accounts.json")


def log(text):
    output.configure(state='normal')
    output.insert(tkinter.END, text + '\n')
    output.configure(state='disabled')
    output.see(tkinter.END)
    
def draw_gradient(canvas, width, height, color1, color2):
    r1, g1, b1 = canvas.winfo_rgb(color1)
    r2, g2, b2 = canvas.winfo_rgb(color2)

    r_ratio = (r2 - r1) / height
    g_ratio = (g2 - g1) / height
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





#_____________________________LOGIC_____________________________

TwitchToken = Functions.get_twitch_token()
gameid = Functions.get_game_id(TwitchToken)
# log(f"Twitch Token: {TwitchToken}")
# log(f"GameID: {gameid}")

def onclick_thread():
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

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except Exception as error:
        log("Failed to load streamer account data: " + str(error))
        return


    found_any = False

    for player, info in data.items():
        accounts = info.get("accounts", [])
        for account in accounts:
            streamername = player
            summonername = account.get("name")
            region = account.get("region")

            try:
                puuid = Functions.get_puuid(summonername, region)
            except Exception:
                continue

            try:
                ChampionInGame = Functions.get_player_champ(puuid, region)
            except Exception:
                continue

            if ChampionInGame:
                try:
                    ChampionInGameName = Functions.get_champion("ChampionName", ChampionInGame)
                except Exception as error:
                    log(f"Error converting champion key to name: {error}")
                    ChampionInGameName = str(ChampionInGame)

                if ChampionInGame == championId:
                    log(f"Streamer: {streamername} is currently playing: {ChampionInGameName}")
                    found_any = True

    if not found_any:
        log(f"No streamers are currently playing {ChampionText}.")


def onclick():
    threading.Thread(target=onclick_thread, daemon=True).start()



                    
                
        

def onclickMap_thread():
    twitchname = TwitchName.get().strip()
    riotname = RiotId.get().strip()
    region = Region.get().strip().lower()

    FoundTwitchProof = False
    FoundRiotProof = False

    ChannelData = Functions.find_channel(twitchname, TwitchToken)
    if ChannelData != "none":
        channelLogin = ChannelData["broadcaster_login"]
        for tag in ChannelData["tags"]:
            if tag.lower() in Functions.tagsTable:
                FoundTwitchProof = True
                log(f"Found Proof for streamer: {channelLogin} via tags")

        if ChannelData["game_id"] == gameid:
            FoundTwitchProof = True
            log(f"Found proof for streamer {channelLogin} via live/recent games played")

    newRegion = Functions.fix_region(region)
    if newRegion == "none":
        log("Region invalid, please insert proper region")
        return

    log(f"Changed region from {region} to {newRegion}")
    routingregion = Functions.get_account_region(newRegion)

    playerpuuid = Functions.get_puuid(riotname, routingregion)
    if playerpuuid:
        FoundRiotProof = True
        log(f"Found Proof for Riot account: {riotname}")

    if FoundTwitchProof and FoundRiotProof:
        Functions.add_streamer_mapping(twitchname, riotname, newRegion)
        log(f"Streamer successfully mapped twitch name: {twitchname}, riot name: {riotname}, region: {newRegion}")


def onclickMap():
    threading.Thread(target=onclickMap_thread, daemon=True).start()

        
    


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
    command=onclick
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
    command=onclickMap
)

mapbutton.bind("<Enter>", on_enter)
mapbutton.bind("<Leave>", on_leave)

canvas.create_window(width // 2, 570, window=mapbutton)


root.mainloop()