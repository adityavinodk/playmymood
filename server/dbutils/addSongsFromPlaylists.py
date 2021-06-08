import base64
import json
import time
from secrets import *

import requests as req
from tqdm import tqdm

message = f"{clientId}:{clientSecret}"
messageBytes = message.encode("ascii")
base64Bytes = base64.b64encode(messageBytes)
base64Message = base64Bytes.decode("ascii")

token = req.post(
    "https://accounts.spotify.com/api/token",
    headers={"Authorization": f"Basic {base64Message}"},
    data={"grant_type": "client_credentials"},
).json()["access_token"]

with open("playlistIds.json", "r") as f:
    data = json.load(f)

failed_points = []
for i in tqdm(range(len(data["ids"]))):
    playlistId = data["ids"][i]
    url = f"https://api.spotify.com/v1/playlists/{playlistId}/tracks"
    playlistReq = req.get(url, headers={"Authorization": "Bearer " + token})
    if playlistReq.status_code == 200:
        playlistData = playlistReq.json()
        for item in playlistData["items"]:
            songId = item["track"]["id"]
            r = req.post(
                "http://127.0.0.1:8000/api/songs/addMetadata",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"id": songId}),
            )
            if r.status_code == 200:
                time.sleep(0.5)
            elif r.status_code == 500:
                failed_points.append(songId)

if len(failed_points):
    for point in failed_points:
        print(point)
