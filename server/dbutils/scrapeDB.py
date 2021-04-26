import pymongo as pym
import json
import sys

if len(sys.argv) != 2:
    print("Enter argument for file name")
    exit()

mergedList = []

my_client = pym.MongoClient()
db = my_client["playMyMood"]

for document in db.datapoints.find():
    del document["_id"]
    mergedList.append(document)

filename = "user-" + sys.argv[1] + ".json"
with open(filename, "w") as f:
    json.dump(mergedList, f, indent=4)
