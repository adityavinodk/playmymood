import base64
import json
import sys
from secrets import *

import numpy as np
import requests as req
from scipy import spatial

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


def printSongMetadata(songId):
    song_data_url = f"https://api.spotify.com/v1/tracks/{songId}"
    song_data_req = req.get(song_data_url, headers={"Authorization": "Bearer " + token})
    if song_data_req.status_code == 200:
        song_data = song_data_req.json()
        return_data = {"name": song_data["name"]}
        song_data = song_data_req.json()
        album_id = song_data["album"]["id"]
        album_data_url = f"https://api.spotify.com/v1/albums/{album_id}"
        album_data_req = req.get(
            album_data_url, headers={"Authorization": "Bearer " + token}
        )
        if album_data_req.status_code == 200:
            album_data = album_data_req.json()
            if len(album_data["genres"]):
                genres = album_data["genres"]
            else:
                all_genres = set()
                for artist in song_data["artists"][:2]:
                    artist_data_url = (
                        f"https://api.spotify.com/v1/artists/{artist['id']}"
                    )
                    artist_data_req = req.get(
                        artist_data_url, headers={"Authorization": "Bearer " + token}
                    )
                    if artist_data_req.status_code == 200:
                        artist_data = artist_data_req.json()
                        all_genres |= set(artist_data["genres"])
                genres = list(all_genres)
                return_data["genres"] = genres
        print(return_data, end="\n\n")


printSongMetadata(sys.argv[1])
printSongMetadata(sys.argv[2])
distance = spatial.distance.cosine(
    getSongMetadata(sys.argv[1]), getSongMetadata(sys.argv[2])
)
print("distance = ", distance, sep="")
