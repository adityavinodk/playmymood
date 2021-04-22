import pymongo as pym
import sys

client = pym.MongoClient()
db = client['playMyMood']

count = 0
for p in db.datapoints.find():
    if count<int(sys.argv[1]):
        print(p)
    count+=1
         