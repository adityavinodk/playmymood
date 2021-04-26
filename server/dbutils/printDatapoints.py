import pymongo as pym
import sys

client = pym.MongoClient()
db = client["playMyMood"]

count = 0
if sys.argv[2] == "songs":
    for p in db.songs.find(sort=[("_id", pym.DESCENDING)]):
        if count < int(sys.argv[1]):
            print(p)
        count += 1
else:
    for p in db.datapoints.find(sort=[("_id", pym.DESCENDING)]):
        if count < int(sys.argv[1]):
            print(p)
        count += 1
