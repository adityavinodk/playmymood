import pymongo as pym
import json
import sys

if len(sys.argv)!=2:
    print("Enter argument for file name")
    exit()

tracksList = []
fitnessList = []

my_client = pym.MongoClient()
db = my_client['playMyMood']

for document in db.songDataPoint.find():
    b = {"songId": document.get("songId"), "timestamp": document.get("timestamp")}
    tracksList.append(b)

for document in db.bodyDataPoint.find():
    b = {"heartrate": document.get("heartrate"), "timestamp": document.get("timestamp")}
    fitnessList.append(b)

filename = "user-"+sys.argv[1]+".json"
with open(filename, "w") as f:
    json.dump({"tracks": tracksList, "hr": fitnessList}, f, indent=4)
