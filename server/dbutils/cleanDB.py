import pymongo as pym
import json
import sys

my_client = pym.MongoClient()
db = my_client['playMyMood']

p = db.songDataPoint.drop()
q = db.bodyDataPoint.drop()
r = db.mergedData.drop()

if p:
    print("listening data deleted")

if q:
    print("fitness data deleted")

if r:
    print("merged data deleted")