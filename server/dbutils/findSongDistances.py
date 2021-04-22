from secrets import *
import requests as req
import json
import base64
from scipy import spatial
import numpy as np
import sys

message = f"{clientId}:{clientSecret}"
messageBytes = message.encode("ascii")
base64Bytes = base64.b64encode(messageBytes)
base64Message = base64Bytes.decode("ascii")

token = req.post(
    "https://accounts.spotify.com/api/token",
    headers={"Authorization": f"Basic {base64Message}"},
    data={"grant_type": "client_credentials"},
).json()["access_token"]


def getSongMetadata(songId):
    url = f"https://api.spotify.com/v1/audio-features/{songId}"
    song_metadata = req.get(url, headers={"Authorization": "Bearer " + token})
    if song_metadata.status_code == 200:
        metadata = song_metadata.json()
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
        return np.array(data)


distance = spatial.distance.cosine(
    getSongMetadata(sys.argv[1]), getSongMetadata(sys.argv[2])
)
print(distance)
