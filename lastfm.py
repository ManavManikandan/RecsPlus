import os
import pytest
import requests     

LASTFM_API_KEY = 'e60d6c99b08a6dae8c073af6dd0ebf2c'
LASTFM_API_SECRET = '0dbd25df91959e5b8f5a7496e381a5f5'


def similarTrack(songName, artistName):
    params = {
        'method': 'track.getsimilar',
        'api_key': LASTFM_API_KEY,
        'artist': artistName,
        'track': songName,      
        'limit': 20,
        'format': 'json'
    }

    response = requests.get('http://ws.audioscrobbler.com/2.0/', params=params)

    if response.status_code == 200:
        data = response.json()
        test = data['similartracks']['track']
        print([f"{t['name']}" for t in test])
        return data
    else:
        print("similarTrack error:", response.status_code)
        return None


#    params = {
#        'method': 'track.getInfo',
#        'api_key': LASTFM_API_KEY,
#        'artist': 'Adrianne Lenker',          # Required unless using mbid
#        'track': 'two reverse',        # Required unless using mbid
#        'format': 'json'
#    }
#
#    response = requests.get('http://ws.audioscrobbler.com/2.0/', params=params)
#
#    if response.status_code == 200:
#        data = response.json()
#        tag = data['track']['toptags']['tag']
#        print([t['name'] for t in tag])
#    else:
#        print("getinfo error:", response.status_code)
