import os
import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, redirect, session, url_for

# Spotify API credentials
CLIENT_ID = 'your_spotify_client_id'
CLIENT_SECRET = 'your_spotify_client_secret'
REDIRECT_URI = 'http://localhost:5000/callback'
SCOPE = 'user-read-playback-state,user-modify-playback-state,user-library-read'

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'

sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE)

@app.route('/')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('randomize_queue'))

def get_spotify_client():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect('/')
    sp = spotipy.Spotify(auth=token_info['access_token'])
    return sp


@app.route('/randomize_queue')
def randomize_queue():
    sp = get_spotify_client()
    if not sp:
        return redirect('/')
    
    playback = sp.current_playback()
    if not playback or not playback['is_playing']:
        return "No music currently playing"

    current_track_id = playback['item']['id']
    queue = sp.current_user_queue()

    # Extract track IDs from the queue
    track_ids = [current_track_id] + [track['id'] for track in queue['tracks']]

    # Randomize the track order
    random.shuffle(track_ids)

    for _ in range(len(track_ids) - 1):
        sp.next_track()

    for track_id in track_ids[1:]:
        sp.add_to_queue(track_id)

    sp.start_playback(uris=[f'spotify:track:{track_ids[0]}'])

    return "Queue randomized successfully!"

if __name__ == '__main__':
    app.run(debug=True)
