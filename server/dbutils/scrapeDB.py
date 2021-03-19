import pymongo as pym
import json
import sys

if len(sys.argv)!=2:
    print("Enter argument for file name")
    exit()

tracksList = []
fitnessList = []
mergedList = []

my_client = pym.MongoClient()
db = my_client['playMyMood']

for document in db.songDataPoint.find():
    b = {"songId": document.get("songId"), "timestamp": document.get("timestamp")}
    tracksList.append(b)

for document in db.bodyDataPoint.find():
    b = {"heartrate": document.get("heartrate"), "timestamp": document.get("timestamp")}
    fitnessList.append(b)

for document in db.datapoints.find():
    mergedList.append(document)

filename = "user-"+sys.argv[1]+".json"
with open(filename, "w") as f:
    json.dump({"tracks": tracksList, "hr": fitnessList, 'datapoints': mergedList}, f, indent=4)
