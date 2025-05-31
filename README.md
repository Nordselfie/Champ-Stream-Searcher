# Champ Stream Searcher

## Table of contents
- [How to use](#HowToUse)
- [How it works](#HowItWorks)

## How to use
Input a champion name
the tool searches for streamers that are playing the champion and returns their names.

## How it works
- get the twitch token
- get the league of legends id on twitch
- when you insert a champion name, strip the text to make sure theres no spaces or special characters
- we get the champion key from ["ddragon"](https://ddragon.leagueoflegends.com/cdn/15.5.1/data/en_US/champion.json)
- we loop through the streamers and all of their accounts in the streamer_accounts.json file
- for each account we request their puuid via riot api
- check if they are in a live game using the puuid
- if so then check what champion they're playing
- if it matches our requested champion
- get their twitch and log it
