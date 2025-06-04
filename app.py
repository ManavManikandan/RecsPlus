from flask import Flask, request, jsonify, session, url_for, redirect, render_template
from flask_cors import CORS  # <-- Add this import
import os
import requests
import base64
from datetime import datetime

import json
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

import urllib.parse
import lastfm 
import Gemini

# Replace these with your app's credentials
CLIENT_ID = os.getenv("SPOTIFY_API_KEY") 
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "https://recsplus.onrender.com/callback"

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'

scope = 'user-library-read, playlist-modify-public, playlist-modify-private'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SPOTIFY_SECRET_KEY')
CORS(app)  # <-- Enable CORS for all routes



# Start of OAuth
@app.route('/')
def index():
    if 'access_token' not in session:
        return redirect('/home')

    if datetime.now().timestamp() > session['expires_in']:
        return redirect('/refresh_token')

    else:
        return render_template("index.html")

@app.route('/logout')
def logout():
    session.pop('access_token', None)
    session.pop('refresh_token', None)
    return redirect('/home')

@app.route('/login')
def login():
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})

    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

    response = requests.post(TOKEN_URL, data=req_body)
    token_info = response.json()

    session['access_token'] = token_info['access_token']
    session['refresh_token'] = token_info['refresh_token']
    session['expires_in']= datetime.now().timestamp() + token_info['expires_in']

    return redirect('/')


@app.route('/recommend', methods=['POST'])
def recommend():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_in']:
        return redirect('/refresh_token')
    
    access_token = session['access_token']

    data = request.get_json()

    print("popularity - ", data.get('popularity'))
    print("emotion - ", data.get('emotion'))

    songInfo = {
        'song_name': data.get('song'),
        'artist': data.get('artist'),
        'tags': data.get('tags'),
        'target_popularity': data.get('popularity'),
        'target_emotion': data.get('emotion')
    }
    print("songInfo: ", songInfo)

    songInfoStr = json.dumps(songInfo)
    print("songInfoStr: ", songInfoStr)

    Recs = Gemini.generate(songInfoStr)
    if Recs == None:
        print("No Gemini Output")

    RecsJSON = json.loads(Recs)
    return jsonify({
        'recommendations': RecsJSON['track']
    })



@app.route('/refresh_token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_in']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_in'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/')



@app.route('/home')
def loginRequired():
    return render_template("authrequired.html")



@app.route('/results')
def results():
    return render_template("recs.html")



def getSearch(query):
    url = f'https://api.spotify.com/v1/search'

    access_token = session['access_token']

    print("access_token: ", access_token)

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    params = {
            'q': query,
        'type': 'track,artist',
        'limit': 5,
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        query_data = response.json()
        print("query_data: ", query_data)
        return query_data
    else: 
        print(f"search error: {response.status_code}")
        return None;




@app.route('/playlist', methods=['POST'])
def playlist():
    url = f'https://api.spotify.com/v1/me'

    access_token = session['access_token']

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, headers=headers)
    response = response.json()

    user_id = response['id']

    print("user id: ", user_id)

    url = f'https://api.spotify.com/v1/users/{user_id}/playlists'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    data = request.get_json()
    body = {
        'name': f"Recs for {data.get('track')} by {data.get('artist')}"
    }

    response = requests.post(url, headers=headers, json=body)
    playlist = response.json()

    playlist_id = playlist['id']

    print("playlist id: ", playlist_id)

    Recs = data.get('recs')
    URI_list = []
    for song in Recs:
        track = getSearch(song['songName'] + ' '  +  song['artistName'])
        URI_list.append(track['tracks']['items'][0]['uri'])

    print(URI_list)

    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    body = {
        'uris': URI_list
    }

    response = requests.post(url, headers=headers, json=body)

    print(response.status_code);

    return jsonify({
        'URL': f"https://open.spotify.com/embed/playlist/{playlist_id}"
    })



@app.route('/search')
def Search():
    if 'access_token' not in session:
        return jsonify({'error': 'User not authenticated'}), 401

    query = request.args.get('q','')
    print("query: ", query)
    result = getSearch(query)
    print(jsonify(result))
    return jsonify(result)

def get_album_details(album_id, access_token):
    url = f'https://api.spotify.com/v1/albums/{album_id}'
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        album_data = response.json()
        return album_data
    else:
        print(f"Error: {response.status_code}")
        return None

def get_album_id(album_name, access_token):  # added access_token
    search_url = 'https://api.spotify.com/v1/search'
    params = {
        'q': album_name,
        'type': 'album',
        'limit': 1
    }

    response = requests.get(
        search_url,
        headers={'Authorization': f'Bearer {access_token}'},
        params=params
    )

    if response.status_code == 200:
        data = response.json()
        if data['albums']['items']:
            return data['albums']['items'][0]['id']
        else:
            print('No albums found')
            return None
    else:
        print(f'Error in get_album_id: {response.status_code}')
        return None



def get_track_details(track_id, access_token):
    url = f'https://api.spotify.com/v1/tracks/{track_id}'
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        track_data = response.json()
        return track_data
    else:
        print(f"get_track_details error: {response.status_code}")
        return None

# new code
def get_track_id(song_name, access_token):  # added access_token
    search_url = 'https://api.spotify.com/v1/search'
    params = {
        'q': song_name,
        'type': 'track',
        'limit': 1
    }

    response = requests.get(
        search_url,
        headers={'Authorization': f'Bearer {access_token}'},
        params=params
    )

    if response.status_code == 200:
        data = response.json()
        if data['tracks']['items']:
            return data['tracks']['items'][0]['id']
        else:
            print('No tracks found')
            return None
    else:
        print(f'Error in get_track_id: {response.status_code}')
        return None

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8888))
    app.run(debug=False, port=port, host='0.0.0.0') 
