from flask import Flask, request, Response, session, render_template
from flask_cors import CORS
import pymongo as pym
import json
import os
import time
import hashlib
import config
import requests as req
import base64
import sys
from secrets import *
from modelUtils import (
    makeTimestampClusters,
    addToTimestampClusters,
    retrieveSimilarSongs,
)
from utils import plainResponse, responseWithData
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
CORS(app)
app.config.from_object(config.Config)
app.secret_key = config.Config.SECRET_KEY
message = f"{clientId}:{clientSecret}"
messageBytes = message.encode("ascii")
base64Bytes = base64.b64encode(messageBytes)
base64Message = base64Bytes.decode("ascii")

if len(sys.argv)>1:
    app.config['USERNAME'] = sys.argv[1]

try:
    my_client = pym.MongoClient(
        app.config["MONGO_URL"],
        serverSelectionTimeoutMS=app.config["SERVER_SELECT_TIMEOUT"],
    )
    print(my_client.server_info())
    print(
        "\n----------------------------------------------------------------\nMongo connected. Starting app...\n---------------------    -------------------------------------------"
    )
    db = my_client["playMyMood"]
    makeTimestampClusters(db, app.config['USERNAME'])
    app.config["RECLUSTER_TIMESTAMP"] = int(time.time())
except pym.errors.ServerSelectionTimeoutError as err:
    print(err)
    print(
        "\n----------------------------------------------------------------\nMongo not connected. Exiting app...\n------------------    -------------------------------------------"
    )
    exit()


@app.route("/api/songs/getSongMetadata", methods=["POST"])
def getSongData():
    req_data = request.get_json()
    if "id" not in req_data:
        return plainResponse("Error: Missing fields in request body", False, 400)
    token = req.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {base64Message}"},
        data={"grant_type": "client_credentials"},
    ).json()["access_token"]
    url = f"https://api.spotify.com/v1/audio-features/{req_data['id']}"
    metadata_req = req.get(url, headers={"Authorization": "Bearer " + token})
    if metadata_req.status_code == 200:
        metadata = metadata_req.json()
        data = [
            metadata["key"],
            metadata["mode"],
            metadata["time_signature"],
            metadata["acousticness"],
            metadata["danceability"],
            metadata["energy"],
            metadata["instrumentalness"],
            metadata["liveness"],
            metadata["loudness"],
            metadata["speechiness"],
            metadata["valence"],
            metadata["tempo"],
        ]
        return responseWithData(
            "Spotify Track data successfully recieved", True, 200, data
        )
    return plainResponse("Server error", False, 500)


@app.route("/api/songs/addMetadata", methods=["POST"])
def add_song_metadata():
    req_data = request.get_json()
    if "id" not in req_data:
        return plainResponse("Error: Missing fields in request body", False, 400)
    if db.songs.find_one({"songId": req_data["id"]}) == None:
        r = req.post(
            "http://127.0.0.1:8000/api/songs/getSongMetadata",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"id": req_data["id"]}),
        )
        if r.status_code == 200:
            metadata = r.json()["data"]
            db.songs.insert_one({"songId": req_data["id"], "metadata": metadata})
            return plainResponse("Song successfully added", True, 200)
        else:
            return plainResponse("Server error", False, 500)
    else:
        return plainResponse("Song already present", False, 409)
    return plainResponse("Server error", False, 500)


@app.route("/api/songs/addCurrentlyPlayingTrack", methods=["POST"])
def add_currently_playing_track():
    req_data = request.get_json()
    if "id" not in req_data:
        return plainResponse("Error: Missing fields in request body", False, 400)
    r = req.post(
        "http://127.0.0.1:8000/api/songs/addMetadata",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"id": req_data["id"]}),
    )
    if r.status_code in [200, 409]:
        now = int(time.time())
        if now - app.config["RECLUSTER_TIMESTAMP"] > 3600:
            makeTimestampClusters(db)
            app.config["RECLUSTER_TIMESTAMP"] = now
        app.config["SONG_ID"] = req_data["id"]
        timeInSec = (
            (time.localtime().tm_hour * 3600)
            + (time.localtime().tm_min * 60)
            + (time.localtime().tm_sec)
        )
        if app.config["HEART_RATE"] != 0:
            data = {
                "timestamp": timeInSec,
                "username": app.config['USERNAME'],
                "HR": app.config["HEART_RATE"],
                "songId": app.config["SONG_ID"],
            }
            added_datapoint = db.datapoints.insert_one(data)
            data["_id"] = added_datapoint.inserted_id
            try:
                addToTimestampClusters(db, data)
            except:
                return plainResponse(
                    "Server error while adding new datapoint", False, 500
                )
        return responseWithData(
            "Song datapoint successfully added",
            True,
            200,
            {"timestamp": now, "songId": req_data["id"]},
        )
    return plainResponse("Server error", False, 500)


@app.route("/api/fitness/addBodyParameterValues", methods=["POST"])
def add_body_parameter_values():
    req_data = request.get_json()
    if "heartrate" not in req_data:
        return plainResponse("Error: Missing fields in request body", False, 400)
    now = int(time.time())
    if now - app.config["RECLUSTER_TIMESTAMP"] > 3600:
        makeTimestampClusters(db)
        app.config["RECLUSTER_TIMESTAMP"] = now
    app.config["HEART_RATE"] = req_data["heartrate"]
    timeInSec = (
        (time.localtime().tm_hour * 3600)
        + (time.localtime().tm_min * 60)
        + (time.localtime().tm_sec)
    )
    if app.config["SONG_ID"] != "":
        data = {
            "timestamp": timeInSec,
            "username": app.config['USERNAME'],
            "HR": app.config["HEART_RATE"],
            "songId": app.config["SONG_ID"],
        }
        added_datapoint = db.datapoints.insert_one(data)
        data["_id"] = added_datapoint.inserted_id
        try:
            addToTimestampClusters(db, data)
        except:
            return plainResponse("Server error while adding new datapoint", False, 500)
    return responseWithData(
        "Fitness parameter value successfully added",
        True,
        200,
        {"timestamp": now, "heartrate": req_data["heartrate"]},
    )


@app.route("/api/songs/recommendations", methods=["GET"])
def retrieve_recommendations():
    now = int(time.time())
    if now - app.config["RECLUSTER_TIMESTAMP"] > 3600:
        makeTimestampClusters(db)
        app.config["RECLUSTER_TIMESTAMP"] = now
    datapoint = db.datapoints.find_one(sort=[("_id", pym.DESCENDING)])
    if datapoint:
        # try:
        data = retrieveSimilarSongs(db, datapoint)
        return responseWithData(
            "Recommendations retrieved successfully", True, 200, data
        )
        # except:
            # return plainResponse(
                # "Server error: can't fetch recommendations, try later", False, 500
            # )

    return plainResponse("Server error: no existing data", False, 500)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def hello(path):
    return "Hello, this domain is used for PlayMyMood project by Aditya Vinod Kumar, PES University"


if __name__ == "__main__":
    app.run(debug=True, port=8000, host="0.0.0.0")
