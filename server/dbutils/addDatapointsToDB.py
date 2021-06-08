import base64
import json
import sys
from secrets import *

import pymongo as pym
import requests as req

message = f"{clientId}:{clientSecret}"
messageBytes = message.encode("ascii")
base64Bytes = base64.b64encode(messageBytes)
base64Message = base64Bytes.decode("ascii")
client = pym.MongoClient()
db = client["playMyMood"]
db.datapoints.drop()
filename = sys.argv[1]
with open(f"dbutils/{filename}", "r") as f:
    f = json.load(f)
    data = f["datapoints"]
    for obj in data:
        r = req.post(
            "http://127.0.0.1:8000/api/songs/addMetadata",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"id": obj["songId"]}),
        )
        db.datapoints.insert_one(obj)
