from secrets import *
import requests as req
import json
import base64

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

for playlistId in data["ids"]:
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
            print(songId, end=" ")
            if r.status_code == 200:
                print("Song Added")
            elif r.status_code == 409:
                print("Song already present")
            else:
                print("Failed")
