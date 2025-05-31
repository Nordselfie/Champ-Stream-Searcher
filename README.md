# Champ Stream Searcher

## Table of contents
- [How to use](#HowToUse)
- [How it works](#HowItWorks)

## How to use
Input a champion name
the tool searches for streamers that are playing the champion and returns their names.

## How it works
- First we get the twitch token
- Then we get the league of legends id on twitch
- when you put a champion name we first strip the text.
- we get the champion key from ["ddragon"](https://ddragon.leagueoflegends.com/cdn/15.5.1/data/en_US/champion.json)
- we loop through the streamers and all of their accounts in the streamer_accounts.json
- for each account we request their puuid via riot api
- check if they are in a live game
- if so then check what champion they're playing
- if it matches our requested champion
- get their twitch and log it
