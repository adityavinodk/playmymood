from flask import Flask, request, Response, session, render_template
from flask_cors import CORS
import pymongo as pym
import json
import os
import hashlib
import config
import requests as req
import base64
from secrets import *
from utils import response
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
CORS(app)
app.config.from_object(config.Config)
app.secret_key = config.Config.SECRET_KEY
message = f"{clientId}:{clientSecret}"
messageBytes = message.encode('ascii')
base64Bytes = base64.b64encode(messageBytes)
base64Message = base64Bytes.decode('ascii')

try:
    my_client = pym.MongoClient(
        app.config["MONGO_URL"],
        serverSelectionTimeoutMS=app.config["SERVER_SELECT_TIMEOUT"],
    )
    print(my_client.server_info())
    print("\n----------------------------------------------------------------\nMongo connected. Starting app...\n---------------------    -------------------------------------------")
    db = my_client["playMyMood"]
except pym.errors.ServerSelectionTimeoutError as err:
    print(err)
    print("\n----------------------------------------------------------------\nMongo not connected. Exiting app...\n------------------    -------------------------------------------")
    exit()

@app.route("/api/songs/addMetadata", methods=["POST"])
def add_song_metadata():
    req_data = request.get_json()
    if 'songId' not in req_data:
        return response("Error: Missing fields in request body", False, 400)
    token = req.post("https://accounts.spotify.com/api/token", headers = {'Authorization': f"Basic {base64Message}"}, data = {'grant_type':'client_credentials'}).json()['access_token']
    url = f"https://api.spotify.com/v1/audio-features/{req_data['songId']}"
    metadata_req = req.post(url, headers = {"Authorization": "Bearer " + token})
    if metadata_req.status_code == 200:
        metadata = metadata_req.json()
        data = [metadata['key'], metadata['mode'], metadata['time_signature'], metadata['acousticness'], metadata['danceability'], metadata['energy'], metadata['instrumentalness'], metadata['liveness'], metadata['loudness'], metadata['speechiness'], metadata['valence'], metadata['tempo']]
        if db.songs.find_one({'songId': req_data['songId']})==None:
            db.songs.insert_one({'songId': req_data['songId'], 'metadata': metadata})
    return response("Song successfully added", True, 200)

@app.route("/api/fitness/addBodyParameterValues", methods=["POST"])
def add_body_parameter_values():
    req_data = request.get_json()
    if 'heartrate' not in req_data or 'timestamp' not in req_data:
        return response("Error: Missing fields in request body", False, 400)
    db.fitness.insert_one(req_data)
    return response("Fitness parameter value successfully added", True, 200)

if __name__ == "__main__":
    app.run(debug=True, port=8000, host="0.0.0.0")
